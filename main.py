from datetime import datetime, timedelta
from typing import Dict, Tuple
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

from pipeline.caption_writer import generate_caption
from services.apherb_catalog import derive_brand_topics, load_brands_from_csv, load_products_from_csv, parse_brand_rss_sources
from services.rss_ingest import ingest_rss
from services.postly_client import create_post
from utils.config import SETTINGS
from utils.logger import (
    append_sheet_log,
    article_seen,
    build_log_payload,
    get_last_products,
    has_posted_today,
    has_scheduled_between,
    init_db,
    log_event,
    log_posted_post,
    log_scheduled_post,
    record_article_check,
    upsert_brand_topics,
)
from pipeline.matcher import select_best_product
from pipeline.safety_filter import safety_filter


def _local_timezone() -> ZoneInfo | None:
    """Return a ZoneInfo instance for the configured timezone, if valid."""
    try:
        return ZoneInfo(SETTINGS.local_timezone)
    except Exception:
        return None


def _local_now() -> datetime:
    """Return current time in the configured local timezone (fallback to naive)."""
    tzinfo = _local_timezone()
    return datetime.now(tz=tzinfo) if tzinfo else datetime.now()


def _day_bounds(local_dt: datetime) -> Tuple[datetime, datetime]:
    """Return start/end bounds for the date of local_dt."""
    start = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def _schedule_time_for_day(local_dt: datetime) -> datetime:
    """Return scheduled time for the date of local_dt."""
    return local_dt.replace(
        hour=SETTINGS.schedule_hour,
        minute=SETTINGS.schedule_minute,
        second=0,
        microsecond=0,
    )


# Log the current outcome to SQLite/Sheets and continue to next item.
def _log_and_continue(entry: Dict, product: Dict, caption: str, status: str,
                      reason: str) -> None:
    """Persist a processing outcome to SQLite and Google Sheets, then continue pipeline."""
    payload = build_log_payload(entry, product, caption, status, reason)
    log_event(SETTINGS.sqlite_path, payload)
    append_sheet_log(SETTINGS.google_sheet_credentials_json,
                     SETTINGS.google_sheet_id, payload)


# Process a single RSS entry end-to-end (safety, match, caption, post).
def _process_entry(
    entry: Dict,
    products: list,
    brand: Dict,
    last_products: list[str],
    scheduled_time: datetime,
    now_local: datetime,
) -> Tuple[bool, str]:
    """Run safety checks, match a product, generate caption, and post/log result."""
    print(f"[pipeline] Evaluating entry: {entry.get('title', '')}")
    entry = {
        **entry,
        "brand_name": brand.get("brand_name", ""),
        "brand_tags": brand.get("tags", ""),
    }
    ok, reason = safety_filter(entry, products)
    if not ok:
        print(f"[pipeline] Safety filter failed: {reason}")
        _log_and_continue(entry, {}, "", "skipped", reason)
        record_article_check(
            SETTINGS.sqlite_path,
            brand.get("brand_name", ""),
            entry.get("title", ""),
            entry.get("url", ""),
            "skipped",
            reason,
        )
        return False, reason

    print("[pipeline] Safety filter passed. Selecting product...")
    product, score = select_best_product(entry, products,
                                         SETTINGS.product_match_threshold)
    if not product:
        print(f"[pipeline] No product match (score={score:.2f}).")
        _log_and_continue(entry, {}, "", "skipped",
                          f"No product match (score={score:.2f})")
        record_article_check(
            SETTINGS.sqlite_path,
            brand.get("brand_name", ""),
            entry.get("title", ""),
            entry.get("url", ""),
            "skipped",
            f"No product match (score={score:.2f})",
        )
        return False, "No product match"

    product_name = product.get("product_name", "")
    if SETTINGS.avoid_repeat_product and last_products and product_name in last_products:
        print("[pipeline] Skipping entry due to repeated product match.")
        return False, "repeat_product"

    print(f"[pipeline] Product matched: {product_name} (score={score:.2f})")
    caption = generate_caption(entry, product)

    if not product.get("product_image_url"):
        print("[pipeline] Missing product image URL.")
        _log_and_continue(entry, product, caption, "failed",
                          "Missing product image URL")
        record_article_check(
            SETTINGS.sqlite_path,
            brand.get("brand_name", ""),
            entry.get("title", ""),
            entry.get("url", ""),
            "failed",
            "Missing product image URL",
        )
        return False, "Missing product image URL"

    if not SETTINGS.postly_api_key:
        print("[pipeline] POSTLY_API_KEY missing; dry run only.")
        _log_and_continue(entry, product, caption, "failed",
                          "Missing POSTLY_API_KEY")
        record_article_check(
            SETTINGS.sqlite_path,
            brand.get("brand_name", ""),
            entry.get("title", ""),
            entry.get("url", ""),
            "failed",
            "Missing POSTLY_API_KEY",
        )
        return False, "Missing POSTLY_API_KEY"

    target_platforms = brand.get("target_platforms", "")
    workspace_ids = brand.get("workspace_ids",
                              "") or SETTINGS.postly_workspace_ids
    if not target_platforms:
        print("[pipeline] Missing target platforms.")
        _log_and_continue(entry, product, caption, "failed",
                          "Missing target platforms")
        record_article_check(
            SETTINGS.sqlite_path,
            brand.get("brand_name", ""),
            entry.get("title", ""),
            entry.get("url", ""),
            "failed",
            "Missing target platforms",
        )
        return False, "Missing target platforms"
    if not workspace_ids:
        print("[pipeline] Missing workspace IDs.")
        _log_and_continue(entry, product, caption, "failed",
                          "Missing workspace IDs")
        record_article_check(
            SETTINGS.sqlite_path,
            brand.get("brand_name", ""),
            entry.get("title", ""),
            entry.get("url", ""),
            "failed",
            "Missing workspace IDs",
        )
        return False, "Missing workspace IDs"

    try:
        scheduled_iso = scheduled_time.isoformat()
        create_post(
            SETTINGS.postly_base_url,
            SETTINGS.postly_api_key,
            caption,
            product.get("product_image_url", ""),
            scheduled_iso,
            target_platforms=target_platforms,
            workspace_ids=workspace_ids,
        )
        status = "posted" if scheduled_time <= now_local else "scheduled"
        post_payload = {
            "brand_name": brand.get("brand_name", ""),
            "product_name": product_name,
            "article_title": entry.get("title", ""),
            "article_url": entry.get("url", ""),
            "image_url": product.get("product_image_url", ""),
            "caption": caption,
            "scheduled_time": scheduled_iso,
            "posted_time":
            now_local.isoformat() if status == "posted" else None,
            "status": status,
        }
        if status == "posted":
            log_posted_post(SETTINGS.sqlite_path, post_payload)
        else:
            log_scheduled_post(SETTINGS.sqlite_path, post_payload)
        _log_and_continue(entry, product, caption, status, "")
        record_article_check(
            SETTINGS.sqlite_path,
            brand.get("brand_name", ""),
            entry.get("title", ""),
            entry.get("url", ""),
            status,
            "",
        )
        return True, status
    except Exception as exc:
        _log_and_continue(entry, product, caption, "failed", str(exc))
        log_scheduled_post(
            SETTINGS.sqlite_path,
            {
                "brand_name": brand.get("brand_name", ""),
                "product_name": product_name,
                "article_title": entry.get("title", ""),
                "article_url": entry.get("url", ""),
                "image_url": product.get("product_image_url", ""),
                "caption": caption,
                "scheduled_time": scheduled_time.isoformat(),
                "posted_time": None,
                "status": "failed",
            },
        )
        record_article_check(
            SETTINGS.sqlite_path,
            brand.get("brand_name", ""),
            entry.get("title", ""),
            entry.get("url", ""),
            "failed",
            str(exc),
        )
        return False, str(exc)


def _schedule_for_brand(
    brand: Dict,
    last_products: list[str],
    products: list,
    entries: list,
    scheduled_time: datetime,
    now_local: datetime,
) -> bool:
    """Find a valid entry and schedule a post for the brand."""
    for entry in entries:
        if article_seen(
                SETTINGS.sqlite_path,
                brand.get("brand_name", ""),
                entry.get("title", ""),
                entry.get("article_url", ""),
        ):
            print("[pipeline] Skipping already-checked article.")
            continue
        print("[pipeline] Processing next entry...")
        posted, reason = _process_entry(entry, products, brand, last_products,
                                        scheduled_time, now_local)
        if reason == "repeat_product":
            continue
        if posted:
            print("[pipeline] Post scheduled successfully. Done.")
            return True
    return False


# Daily pipeline runner: ingest feeds, load catalog, and post first valid item.
def run_daily() -> None:
    """Main daily workflow: ingest RSS, scrape catalog, and post the first valid article per brand."""
    print("[pipeline] Initializing database...")
    init_db(SETTINGS.sqlite_path)
    brands = load_brands_from_csv(SETTINGS.brands_csv_path)
    if not brands:
        print("[pipeline] No brands found in Brands.csv.")
        _log_and_continue({}, {}, "", "failed", "Brands.csv is empty")
        return

    for brand in brands:
        brand_name = brand.get("brand_name", "Unknown")
        print(f"[pipeline] Processing brand: {brand_name}")
        product_csv = brand.get(
            "product_info_csv_path") or SETTINGS.product_info_csv_path
        print(f"[pipeline] Loading product catalog for {brand_name}...")
        products = load_products_from_csv(product_csv)
        if not products:
            print(f"[pipeline] Product catalog empty for {brand_name}.")
            _log_and_continue({}, {}, "", "failed",
                              f"Product catalog empty for {brand_name}")
            continue

        topics_payload = derive_brand_topics(products)
        topics_payload["brand_name"] = brand_name
        topics_payload["updated_at"] = datetime.utcnow().isoformat()
        upsert_brand_topics(SETTINGS.sqlite_path, topics_payload)

        brand_sources = parse_brand_rss_sources(brand.get("rss_sources", ""))
        sources = brand_sources or SETTINGS.rss_sources
        print(f"[pipeline] Ingesting RSS feeds for {brand_name}...")
        entries = ingest_rss(sources)
        print(f"[pipeline] RSS entries loaded: {len(entries)}")

        now_local = _local_now()
        today_start, today_end = _day_bounds(now_local)
        tomorrow_start, tomorrow_end = _day_bounds(now_local +
                                                   timedelta(days=1))
        posted_today = has_posted_today(
            SETTINGS.sqlite_path,
            brand_name,
            today_start.isoformat(),
            today_end.isoformat(),
        )
        last_products = get_last_products(
            SETTINGS.sqlite_path,
            brand_name,
            SETTINGS.avoid_repeat_product_count,
        )
        if posted_today:
            if has_scheduled_between(
                    SETTINGS.sqlite_path,
                    brand_name,
                    tomorrow_start.isoformat(),
                    tomorrow_end.isoformat(),
            ):
                print(
                    f"[pipeline] Tomorrow already scheduled for {brand_name}.")
                continue
            scheduled_time = _schedule_time_for_day(tomorrow_start)
            scheduled = _schedule_for_brand(brand, last_products, products,
                                            entries, scheduled_time, now_local)
        else:
            scheduled_time = _schedule_time_for_day(today_start)
            if now_local >= scheduled_time:
                scheduled_time = now_local
            scheduled = _schedule_for_brand(brand, last_products, products,
                                            entries, scheduled_time, now_local)

        if not scheduled:
            print(f"[pipeline] No valid articles found for {brand_name}.")
            _log_and_continue({}, {}, "", "failed",
                              f"No valid articles found for {brand_name}")


if __name__ == "__main__":
    print(
        f"[pipeline] Job started at {datetime.now(timezone.utc).isoformat()} UTC"
    )
    run_daily()
    print(
        f"[pipeline] Job finished at {datetime.now(timezone.utc).isoformat()} UTC"
    )

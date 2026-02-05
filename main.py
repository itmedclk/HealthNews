from datetime import datetime
from typing import Dict, Tuple

from apherb_catalog import derive_brand_topics, load_brands_from_csv, load_products_from_csv, parse_brand_rss_sources
from caption_writer import generate_caption
from config import SETTINGS
from logger import append_sheet_log, build_log_payload, init_db, log_event, upsert_brand_topics
from matcher import select_best_product
from postly_client import create_post
from rss_ingest import ingest_rss
from safety_filter import safety_filter


# Build the ISO timestamp for today's scheduled post time.
def _schedule_iso() -> str:
    """Build an ISO timestamp for today's scheduled post time."""
    now = datetime.now()
    scheduled = now.replace(hour=SETTINGS.schedule_hour, minute=SETTINGS.schedule_minute, second=0, microsecond=0)
    return scheduled.isoformat()


# Log the current outcome to SQLite/Sheets and continue to next item.
def _log_and_continue(entry: Dict, product: Dict, caption: str, status: str, reason: str) -> None:
    """Persist a processing outcome to SQLite and Google Sheets, then continue pipeline."""
    payload = build_log_payload(entry, product, caption, status, reason)
    log_event(SETTINGS.sqlite_path, payload)
    append_sheet_log(SETTINGS.google_sheet_credentials_json, SETTINGS.google_sheet_id, payload)


# Process a single RSS entry end-to-end (safety, match, caption, post).
def _process_entry(entry: Dict, products: list, brand: Dict) -> Tuple[bool, str]:
    """Run safety checks, match a product, generate caption, and post/log result."""
    print(f"[pipeline] Evaluating entry: {entry.get('title', '')}")
    ok, reason = safety_filter(entry, products)
    if not ok:
        print(f"[pipeline] Safety filter failed: {reason}")
        _log_and_continue(entry, {}, "", "skipped", reason)
        return False, reason

    print("[pipeline] Safety filter passed. Selecting product...")
    product, score = select_best_product(entry, products, SETTINGS.product_match_threshold)
    if not product:
        print(f"[pipeline] No product match (score={score:.2f}).")
        _log_and_continue(entry, {}, "", "skipped", f"No product match (score={score:.2f})")
        return False, "No product match"

    print(f"[pipeline] Product matched: {product.get('product_name', '')} (score={score:.2f})")
    caption = generate_caption(entry, product)

    if not product.get("product_image_url"):
        print("[pipeline] Missing product image URL.")
        _log_and_continue(entry, product, caption, "failed", "Missing product image URL")
        return False, "Missing product image URL"

    if not SETTINGS.postly_api_key:
        print("[pipeline] POSTLY_API_KEY missing; dry run only.")
        _log_and_continue(entry, product, caption, "failed", "Missing POSTLY_API_KEY")
        return False, "Missing POSTLY_API_KEY"

    try:
        create_post(
            SETTINGS.postly_base_url,
            SETTINGS.postly_api_key,
            caption,
            product.get("product_image_url", ""),
            _schedule_iso(),
            target_platforms=brand.get("target_platforms", ""),
            workspace_ids=brand.get("workspace_ids", ""),
        )
        _log_and_continue(entry, product, caption, "posted", "")
        return True, "posted"
    except Exception as exc:
        _log_and_continue(entry, product, caption, "failed", str(exc))
        return False, str(exc)


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
        product_csv = brand.get("product_info_csv_path") or SETTINGS.product_info_csv_path
        print(f"[pipeline] Loading product catalog for {brand_name}...")
        products = load_products_from_csv(product_csv)
        if not products:
            print(f"[pipeline] Product catalog empty for {brand_name}.")
            _log_and_continue({}, {}, "", "failed", f"Product catalog empty for {brand_name}")
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

        posted = False
        for entry in entries:
            print("[pipeline] Processing next entry...")
            posted, _ = _process_entry(entry, products, brand)
            if posted:
                print("[pipeline] Post scheduled successfully. Done.")
                break
        if not posted:
            print(f"[pipeline] No valid articles found for {brand_name}.")
            _log_and_continue({}, {}, "", "failed", f"No valid articles found for {brand_name}")


if __name__ == "__main__":
    run_daily()

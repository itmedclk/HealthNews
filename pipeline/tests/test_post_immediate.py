from datetime import datetime

from pipeline.caption_writer import generate_caption
from pipeline.matcher import select_best_product
from pipeline.safety_filter import safety_filter
from services.catalog_service import load_brands_from_csv, load_products_from_csv, parse_brand_rss_sources
from services.postly_client import create_post
from services.rss_ingest import ingest_rss
from utils.config import SETTINGS
from utils.logger import init_db, log_posted_post


def main() -> None:
    """Immediately schedule a post for the first valid article/product for the first brand."""
    print("[test] Initializing database...")
    init_db(SETTINGS.sqlite_path)
    brands = load_brands_from_csv(SETTINGS.brands_csv_path)
    if not brands:
        print("[test] No brands found in Brands.csv.")
        return

    brand = brands[0]
    brand_name = brand.get("brand_name", "Unknown")
    print(f"[test] Using brand: {brand_name}")

    product_csv = brand.get("product_info_csv_path") or SETTINGS.product_info_csv_path
    products = load_products_from_csv(product_csv)
    if not products:
        print(f"[test] Product catalog empty for {brand_name}.")
        return
    print(f"[test] Loaded {len(products)} products from {product_csv}.")

    brand_sources = parse_brand_rss_sources(brand.get("rss_sources", ""))
    sources = brand_sources or SETTINGS.rss_sources
    entries = ingest_rss(sources)
    print(f"[test] RSS entries loaded: {len(entries)}")

    target_platforms = brand.get("target_platforms", "")
    workspace_ids = brand.get("workspace_ids", "") or SETTINGS.postly_workspace_ids
    if not target_platforms or not workspace_ids:
        print("[test] Missing target_platforms or workspace_ids.")
        return

    for index, entry in enumerate(entries, start=1):
        entry = {**entry, "brand_name": brand_name, "brand_tags": brand.get("tags", "")}
        print(f"[test] Checking entry {index}/{len(entries)}: {entry.get('title', '')}")
        ok, reason = safety_filter(entry, products)
        if not ok:
            print(f"[test] Safety filter failed: {reason}")
            continue
        print("[test] Safety filter passed.")

        product, score = select_best_product(entry, products, SETTINGS.product_match_threshold)
        if not product:
            print(f"[test] No product match (score={score:.2f}).")
            continue
        print(
            f"[test] Product matched: {product.get('product_name', '')} (score={score:.2f})"
        )

        caption = generate_caption(entry, product)
        image_url = product.get("product_image_url", "")
        print(f"[test] Image URL: {image_url or '[missing]'}")
        if not image_url:
            print("[test] Missing product image URL. Skipping entry.")
            continue

        scheduled_time = datetime.utcnow().isoformat()
        print(f"[test] Scheduling time (UTC): {scheduled_time}")
        try:
            response = create_post(
                SETTINGS.postly_base_url,
                SETTINGS.postly_api_key,
                caption,
                image_url,
                scheduled_time,
                target_platforms=target_platforms,
                workspace_ids=workspace_ids,
            )
            print(f"[test] Postly response: {response}")
        except Exception as exc:
            print(f"[test] Postly API error: {exc}")
            return

        log_posted_post(
            SETTINGS.sqlite_path,
            {
                "brand_name": brand_name,
                "product_name": product.get("product_name", ""),
                "article_title": entry.get("title", ""),
                "article_url": entry.get("url", ""),
                "image_url": image_url,
                "caption": caption,
                "scheduled_time": scheduled_time,
                "posted_time": scheduled_time,
                "status": "posted",
            },
        )
        print("[test] Post scheduled immediately.")
        return

    print("[test] No valid article/product pair found.")


if __name__ == "__main__":
    main()
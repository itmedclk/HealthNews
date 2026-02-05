from datetime import datetime

from pipeline.matcher import select_best_product
from pipeline.safety_filter import safety_filter
from services.apherb_catalog import load_brands_from_csv, load_products_from_csv, parse_brand_rss_sources
from services.rss_ingest import ingest_rss
from utils.config import SETTINGS
from utils.logger import clear_post_log, get_last_products, init_db, log_posted_post


def main() -> None:
    """Test avoid-repeat-product behavior by seeding post_log and selecting a new product."""
    init_db(SETTINGS.sqlite_path)
    brands = load_brands_from_csv(SETTINGS.brands_csv_path)
    if not brands:
        print("[test] No brands found in Brands.csv.")
        return

    brand = brands[0]
    brand_name = brand.get("brand_name", "Unknown")
    clear_post_log(SETTINGS.sqlite_path, brand_name)
    product_csv = brand.get("product_info_csv_path") or SETTINGS.product_info_csv_path
    products = load_products_from_csv(product_csv, resolve_images=False)
    if len(products) < 2:
        print("[test] Need at least 2 products to test repeat avoidance.")
        return

    now_iso = datetime.utcnow().isoformat()
    seeded = []
    for product in products:
        name = product.get("product_name", "").lower()
        if "blood pressure" in name:
            seeded.append(product)
            break
    if len(seeded) < SETTINGS.avoid_repeat_product_count:
        for product in products:
            if product in seeded:
                continue
            seeded.append(product)
            if len(seeded) >= SETTINGS.avoid_repeat_product_count:
                break
    for product in seeded:
        log_posted_post(
            SETTINGS.sqlite_path,
            {
                "brand_name": brand_name,
                "product_name": product.get("product_name", ""),
                "article_title": "seeded",
                "article_url": "seeded",
                "image_url": product.get("product_image_url", ""),
                "caption": "seeded",
                "scheduled_time": now_iso,
                "posted_time": now_iso,
                "status": "posted",
            },
        )

    last_products = get_last_products(
        SETTINGS.sqlite_path,
        brand_name,
        SETTINGS.avoid_repeat_product_count,
    )
    print(f"[test] Last products: {last_products}")

    brand_sources = parse_brand_rss_sources(brand.get("rss_sources", ""))
    sources = brand_sources or SETTINGS.rss_sources
    entries = ingest_rss(sources)
    print(f"[test] Searching {len(entries)} RSS entries for eligible product...")
    for index, entry in enumerate(entries, start=1):
        entry = {**entry, "brand_name": brand_name, "brand_tags": brand.get("tags", "")}
        print(f"[test] Checking entry {index}/{len(entries)}: {entry.get('title', '')}")
        ok, reason = safety_filter(entry, products)
        if not ok:
            print(f"[test] Skipping due to safety filter: {reason}")
            continue
        product, score = select_best_product(entry, products, SETTINGS.product_match_threshold)
        if not product:
            print(f"[test] Skipping due to no product match (score={score:.2f}).")
            continue
        product_name = product.get("product_name", "")
        if product_name in last_products:
            print(f"[test] Skipping repeated product: {product_name}")
            continue
        print(f"[test] Selected product: {product_name} (score={score:.2f})")
        return

    print("[test] No alternative product found. Consider adding more products.")


if __name__ == "__main__":
    main()
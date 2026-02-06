from pprint import pprint

from pipeline.caption_writer import generate_caption
from pipeline.matcher import select_best_product
from pipeline.safety_filter import safety_filter
from services.catalog_service import load_brands_from_csv, load_products_from_csv, parse_brand_rss_sources
from services.rss_ingest import ingest_rss
from utils.config import SETTINGS


def main() -> None:
    """Preview the next post by printing article, product, caption, and image URL."""
    brands = load_brands_from_csv(SETTINGS.brands_csv_path)
    if not brands:
        print("[preview] No brands found in Brands.csv.")
        return
    print(f"[preview] Loaded brands: {len(brands)}")
    for brand in brands:
        brand_name = brand.get("brand_name", "Unknown")
        product_csv = brand.get("product_info_csv_path") or SETTINGS.product_info_csv_path
        brand_sources = parse_brand_rss_sources(brand.get("rss_sources", ""))
        sources = brand_sources or SETTINGS.rss_sources
        print(f"[preview] Loading RSS entries for {brand_name}...")
        entries = ingest_rss(sources)
        print(f"[preview] RSS entries loaded: {len(entries)}")
        print(f"[preview] Loading product catalog for {brand_name}...")
        products = load_products_from_csv(product_csv)
        print(f"[preview] Product match threshold: {SETTINGS.product_match_threshold}")
        print(f"[preview] AI relevance threshold: {SETTINGS.relevance_threshold}")
        for entry in entries:
            entry = {**entry, "brand_name": brand_name, "brand_tags": brand.get("tags", "")}
            print(f"[preview] Evaluating entry: {entry.get('title', '')}")
            ok, reason = safety_filter(entry, products)
            if not ok:
                print(f"[preview] Safety filter failed: {reason}")
                continue
            print("[preview] Safety filter passed. Selecting product...")
            product, score = select_best_product(entry, products, SETTINGS.product_match_threshold)
            if not product:
                print(f"[preview] No product match (score={score:.2f}).")
                continue
            caption = generate_caption(entry, product)
            print("=== BRAND ===")
            pprint(brand)
            print("=== ARTICLE ===")
            pprint(entry)
            print("=== PRODUCT ===")
            pprint(product)
            print("=== SCORE ===")
            print(score)
            print("=== CAPTION ===")
            print(caption)
            return
        print(f"[preview] No valid article/product pair found for {brand_name}.")


if __name__ == "__main__":
    main()
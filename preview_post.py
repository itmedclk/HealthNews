from pprint import pprint

from apherb_catalog import load_products_from_csv
from caption_writer import generate_caption
from config import SETTINGS
from matcher import select_best_product
from rss_ingest import ingest_rss
from safety_filter import safety_filter


def main() -> None:
    """Preview the next post by printing article, product, caption, and image URL."""
    print("[preview] Loading RSS entries...")
    entries = ingest_rss(SETTINGS.rss_sources)
    print(f"[preview] RSS entries loaded: {len(entries)}")
    print("[preview] Loading product catalog...")
    products = load_products_from_csv(SETTINGS.product_info_csv_path)
    print(f"[preview] Product match threshold: {SETTINGS.product_match_threshold}")
    print(f"[preview] AI relevance threshold: {SETTINGS.relevance_threshold}")
    for entry in entries:
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
        print("=== ARTICLE ===")
        pprint(entry)
        print("=== PRODUCT ===")
        pprint(product)
        print("=== SCORE ===")
        print(score)
        print("=== CAPTION ===")
        print(caption)
        return
    print("No valid article/product pair found for preview.")


if __name__ == "__main__":
    main()
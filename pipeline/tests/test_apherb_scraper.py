from pprint import pprint

from services.apherb_catalog import load_products_from_csv
from utils.config import SETTINGS


def main() -> None:
    """Run the AP Herb scraper and print a quick sample of results."""
    products = load_products_from_csv(SETTINGS.product_info_csv_path)
    print(f"Products scraped: {len(products)}")
    pprint(products[:5])


if __name__ == "__main__":
    main()
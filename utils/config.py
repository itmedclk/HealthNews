import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    """Centralized configuration loaded from environment variables."""
    rss_sources: List[str] = field(
        default_factory=lambda: [
            "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
            "https://www.medicalnewstoday.com/rss",
            "https://www.sciencedaily.com/rss/health_medicine.xml",
            "https://www.cdc.gov/media/rss.xml",
            "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
            "https://www.nih.gov/feed",
            "https://www.health.com/feed",
            "https://news.google.com/rss/search?q=eye+health&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=brain+health&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=gout+health&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=blood+pressure+health&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=blood+sugar+health&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=muscle+pain+relief+health&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=joint+pain+relief+health&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=digestive+health&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=digestive+health&hl=en-US&gl=US&ceid=US:en",
            "https://www.sciencedaily.com/rss/top/health.xml ",
            "https://www.naturalproductsinsider.com/rss.xml"
        ]
    )
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    novita_api_key: str = os.getenv("NOVITA_API_KEY", "")
    postly_api_key: str = os.getenv("POSTLY_API_KEY", "")
    postly_base_url: str = os.getenv("POSTLY_BASE_URL", "https://openapi.postly.ai")
    postly_workspace_ids: str = os.getenv("POSTLY_WORKSPACE_IDS", "")
    local_timezone: str = os.getenv("LOCAL_TIMEZONE", "America/Los_Angeles")
    schedule_hour: int = int(os.getenv("SCHEDULE_HOUR", "5"))
    schedule_minute: int = int(os.getenv("SCHEDULE_MINUTE", "0"))
    ap_herb_catalog_url: str = "https://www.apherb.com/goods_list"
    catalog_cache_path: str = "data/catalog_cache.json"
    catalog_cache_ttl_days: int = int(os.getenv("CATALOG_CACHE_TTL_DAYS", "7"))
    sqlite_path: str = os.getenv("SQLITE_PATH", "data/logs.sqlite")
    google_sheet_id: str = os.getenv("GOOGLE_SHEET_ID", "")
    google_sheet_credentials_json: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
    caption_min_words: int = 100
    caption_max_words: int = 150
    hard_block_topics: List[str] = field(
        default_factory=lambda: [
            "pregnancy",
            "children",
            "cancer",
            "diabetes",
            "mental health",
            "sexual health",
        ]
    )
    product_info_csv_path: str = os.getenv("PRODUCT_INFO_CSV_PATH", "info/Product_Info.csv")
    brands_csv_path: str = os.getenv("BRANDS_CSV_PATH", "info/Brands.csv")
    dropbox_image_prefix: str = os.getenv("DROPBOX_IMAGE_PREFIX", "")
    dropbox_access_token: str = os.getenv("DROPBOX_ACCESS_TOKEN", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    novita_base_url: str = os.getenv("NOVITA_BASE_URL", "https://api.novita.ai/openai")
    novita_model: str = os.getenv("NOVITA_MODEL", "deepseek/deepseek-v3.2")
    relevance_threshold: float = float(os.getenv("RELEVANCE_THRESHOLD", "0.4"))
    product_match_threshold: float = float(os.getenv("PRODUCT_MATCH_THRESHOLD", "0.1"))
    use_ai_rerank: bool = os.getenv("USE_AI_RERANK", "true").lower() == "true"
    ai_rerank_top_n: int = int(os.getenv("AI_RERANK_TOP_N", "5"))
    avoid_repeat_product: bool = os.getenv("AVOID_REPEAT_PRODUCT", "true").lower() == "true"
    avoid_repeat_product_count: int = int(os.getenv("AVOID_REPEAT_PRODUCT_COUNT", "2"))


SETTINGS = Settings()

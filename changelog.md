# Changelog

## 2026-02-06
- Added commitment to include a 'What I changed and why' summary after each completion.
- Added Sentry monitoring support (SENTRY_DSN, utils/monitoring.py, and entry-point initialization).
- Added verbose step-by-step logging in test_post_immediate for easier debugging.

## 2026-02-05
- Renamed services/apherb_catalog.py to services/catalog_service.py for multi-brand support.
- Added DROPBOX_IMAGE_PREFIX setting to prepend a shared Dropbox folder root before image_path values.
- Added Dropbox refresh token force-refresh and automatic retry on expired_access_token responses.
- Updated matcher scoring to use weighted keyword fields with noise-token filtering and optional AI rerank.
- Added test_avoid_repeat_product.py for repeat-product checks and clear_post_log helper.
- Added AVOID_REPEAT_PRODUCT_COUNT setting to configure the product repeat window.
- Added AVOID_REPEAT_PRODUCT setting and post_log product_name tracking to avoid repeating recent products.
- Added brand tags column in Brands.csv and appended tags to caption hashtags.
- Added post_log table with scheduling/posted tracking and today/tomorrow scheduling logic.
- Added test_post_immediate.py for immediate Postly posting tests.
- Added Dropbox refresh-token helper and reorganized modules into services/pipeline/utils folders.
- Added article history table and skip logic to avoid re-checking already processed articles.
- Added multi-brand support via Brands.csv, per-brand RSS overrides, and Postly target/workspace routing.
- Persisted brand topic metadata (derived from product categories/tags) into SQLite.

## 2026-02-04
- Switched AP Herb catalog ingestion to CSV (`Product_Info.csv`).
- Added Dropbox API image lookup using per-product `image_path`.
- Introduced new config settings: `PRODUCT_INFO_CSV_PATH` and `DROPBOX_ACCESS_TOKEN`.
- Updated `main.py` and `test_apherb_scraper.py` to use the CSV loader.
- Updated `plan.md` to document CSV + Dropbox workflow.
- Added per-product image rotation stored in `data/image_rotation.json` so images cycle across runs.
- Added `.env.example` to document required environment variables for local/Replit runs.
- Added `preview_post.py` to print the next article/product/caption/image without posting.
- Added AI relevance safety check using the product catalog to filter unrelated articles.
- Switched AI relevance checks to NovitaAI (OpenAI-compatible endpoint and model config).
- Split AI checks into hard-block topic classifier and product relevance scorer with a configurable threshold.
- Updated caption source line to use the article URL and added product match threshold controls.
- Added NovitaAI reranking for top product candidates with configurable toggles.
- Added console logging for pipeline and preview steps to show progress.
- Improved caption source fallback to use article URL or RSS source and added preview threshold logs.
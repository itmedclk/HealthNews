# Changelog

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
# Automated Health News → Instagram (AP Herb) — Design & Implementation Guide

## 1) Purpose & Outcomes
**Goal**: Automatically publish daily health news posts (image + caption) at **5:00 AM local time**, using brand-specific product catalogs and Postly.ai scheduling.

**Primary outcomes**
- One scheduled/posted Instagram entry per brand per day
- Brand-specific product match, image, and hashtags
- Safety screening and logging for every article checked

**Success criteria**
- Posts appear daily at 5:00 AM (or immediately if the job runs after 5 AM)
- Captions follow length and safety rules (100–150 words, educational tone)
- All outcomes logged (posted/scheduled/skipped/failed)

---

## 2) System Overview (End-to-End Flow)
1. **Load brands** from `Brands.csv` and their product catalogs.
2. **Fetch RSS feeds** (brand-specific overrides or global defaults).
3. **Filter articles** (hard-block + AI safety + AI relevance).
4. **Match products** (keyword scoring + optional AI rerank).
5. **Generate caption** (NovitaAI/OpenAI-compatible endpoint).
6. **Schedule post** in Postly at local 5:00 AM.
7. **Log** all results to SQLite + Google Sheets (optional).

If any step fails (safety, relevance, missing config), the pipeline **skips to the next entry**.

---

## 3) Project Structure
```
/project-root
├── main.py                # Daily pipeline runner
├── services/              # External integrations
│   ├── catalog_service.py  # Catalog loading + Dropbox images
│   ├── postly_client.py   # Postly API client
│   └── rss_ingest.py      # RSS fetching + normalization
├── pipeline/              # Pipeline logic
│   ├── caption_writer.py  # Caption generation rules
│   ├── matcher.py         # Product matching + AI rerank
│   ├── preview_post.py    # Preview next post without posting
│   └── safety_filter.py   # Safety + relevance checks
├── utils/                 # Shared helpers
│   ├── config.py          # Environment settings
│   ├── dropbox_auth.py    # Dropbox token refresh helper
│   └── logger.py          # SQLite + Sheets logging
└── requirements.txt
```

---

## 4) Brand & Product Data Design
**Brands source**: `info/Brands.csv`

Required columns:
- `brand_name`
- `target_platforms` (Postly channels)
- `workspace_ids` (fallback to `POSTLY_WORKSPACE_IDS`)
- `tags` (pipe-delimited hashtags)

Optional columns:
- `product_info_csv_path`
- `rss_sources` (pipe-delimited override list)

**Product catalog**: CSV per brand (defaults to `info/Product_Info.csv`).

Key fields used in matching/captioning:
- `product_name`, `product_url`, `description`, `key_ingredients`, `main_benefit`, `category`, `sub_category`, `tags`, `image_path`

---

## 5) Dropbox Image Resolution
- Image folders are listed via the Dropbox API using `image_path`.
- Image files are sorted and rotated using `data/image_rotation.json`.
- A shared link is created and converted to a direct-download URL.
- **Token refresh**: access tokens are refreshed via `DROPBOX_REFRESH_TOKEN` and the API call is retried once on `expired_access_token`.
- **Prefix support**: set `DROPBOX_IMAGE_PREFIX` (e.g. `/healthnews`) to prepend a common folder root before each `image_path`.

Fallback behavior:
- Missing Dropbox config → `image_url` is blank and the entry fails later.
- Empty folder → `no_files_found` status recorded.

---

## 6) RSS Ingestion Logic
Modules: `services/rss_ingest.py`

Steps:
1. Fetch all RSS entries.
2. Normalize fields: `title`, `summary`, `article_url`, `published`.
3. Dedupe by `(title, url)` key.
4. Sort newest-first.

---

## 7) Safety & Relevance Checks
Module: `pipeline/safety_filter.py`

**Hard-block topics** (code-level): pregnancy, children, cancer, diabetes, mental health, sexual health.

**AI checks** (NovitaAI/OpenAI-compatible):
- Hard-block classifier
- Product relevance classifier (must exceed `RELEVANCE_THRESHOLD`)

If any check fails, the entry is skipped and logged.

---

## 8) Product Matching Logic
Module: `pipeline/matcher.py`

**Keyword scoring**:
- Tokenize article title + summary (noise tokens removed).
- Weighted fields: `product_name` (3.0), `main_benefit` (2.5), `category` (2.0), `ingredients` (2.0), `description` (1.0).
- Normalize by entry length.

**Optional AI rerank**:
- Top-N candidates are reranked by NovitaAI.

If the score is below `PRODUCT_MATCH_THRESHOLD`, the entry is skipped.

---

## 9) Caption Generation Rules
Module: `pipeline/caption_writer.py`

Caption structure (enforced in prompt):
1. News summary + why it matters
2. Educational product tie-in (no sales language)
3. `Learn more:` + product URL
4. `Source:` + article URL
5. Exactly 10 hashtags (brand + product tags)

Safety enforcement:
- 100–150 words
- Educational tone only
- No medical advice or cure claims

---

## 10) Scheduling & Daily Execution
Module: `main.py`

Scheduling logic per brand:
- If a post was already **posted today**, schedule the next for **tomorrow at 5:00 AM** (if not already scheduled).
- If no post today:
  - Schedule for **today at 5:00 AM** (or immediately if the job runs after 5 AM).

The pipeline checks each RSS entry until a valid post is scheduled or all entries fail.

---

## 11) Logging & Persistence
Module: `utils/logger.py`

SQLite tables:
- `logs`: all outcomes (posted/skipped/failed)
- `article_history`: skips already-checked articles
- `post_log`: scheduled/posted tracking (used for repeat-product and schedule logic)
- `brands`: derived brand topics

Optional Google Sheets logging:
- Controlled by `GOOGLE_SHEETS_CREDENTIALS_JSON` + `GOOGLE_SHEET_ID`.

Optional error monitoring:
- `SENTRY_DSN` enables Sentry error reporting via `utils/monitoring.py`.

---

## 12) Configuration & Secrets
All settings are loaded from environment variables in `utils/config.py`.

Required for full automation:
- `POSTLY_API_KEY`
- `DROPBOX_REFRESH_TOKEN`
- `DROPBOX_CLIENT_ID`
- `DROPBOX_CLIENT_SECRET`

Optional:
- `POSTLY_WORKSPACE_IDS`
- `BRANDS_CSV_PATH`, `PRODUCT_INFO_CSV_PATH`
- `NOVITA_API_KEY`, `NOVITA_MODEL`, `NOVITA_BASE_URL`
- `RELEVANCE_THRESHOLD`, `PRODUCT_MATCH_THRESHOLD`
- `AVOID_REPEAT_PRODUCT`, `AVOID_REPEAT_PRODUCT_COUNT`
- `DROPBOX_IMAGE_PREFIX`

---

## 13) Operational Tools
- **main.py**: full daily run (scheduled or on-demand)
- **pipeline/preview_post.py**: prints the next valid post without scheduling

---

## 14) Key Design Decisions (Logic Summary)
- **Brand-first pipeline**: each brand is processed independently.
- **Safety-first flow**: safety checks occur before any product matching or captioning.
- **AI optionality**: AI rerank and AI safety are controlled by API availability + config flags.
- **Resilience**: failures are logged and pipeline continues to the next entry.
- **Token refresh**: Dropbox access tokens auto-refresh and retry once on expiry.




























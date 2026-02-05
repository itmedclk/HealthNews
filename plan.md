# Automated Health News → Instagram (AP Herb) — Project Plan

## 1) Goal, Deliverables, Success Criteria, Constraints
**Goal**: Build a Python 3.11+ Replit app that automatically posts daily health news to Instagram at **5:00 AM local time**, using **AP Herb** products and **Postly.ai**.

**Deliverables**
- `plan.md` (this document)
- Replit-ready Python project (to be generated after plan approval)
- Daily automation pipeline with logging

**Success Criteria**
- Posts appear daily at 5:00 AM with image + caption
- Uses **only AP Herb** product data
- Enforces exclusions and safety rules
- Captions are 100–150 words, English, educational tone
- Logs all outcomes (posted/skipped/failed)

**Constraints**
- Use OpenAI for AI tasks
- Post via `POST https://openapi.postly.ai/v1/posts`
- All secrets stored in Replit Secrets

---

## 2) High-Level Architecture (Daily Flow)
1. **RSS Ingest** → pull multiple health feeds, dedupe, newest-first
2. **Safety Filter** → hard-block excluded topics + AI safety classifier
3. **Caption Writer** → AI rewrite to IG format (100–150 words)
4. **AP Herb Catalog** → load from CSV + Dropbox image lookup
5. **Product Matcher** → score products + optional AI ranking
6. **Postly Publish** → schedule post for 5:00 AM
7. **Logging** → write SQLite log entries

If an item fails safety or matching, **skip to next item**.

---

## 3) Recommended Replit File Structure
```
/project-root
├── main.py                # Daily execution entry point
├── config.py              # Settings and constants
├── rss_ingest.py          # RSS feed ingestion
├── apherb_catalog.py      # AP Herb product CSV loader + Dropbox images
├── safety_filter.py       # Topic and claim filtering (AI-assisted)
├── matcher.py             # Product matching logic (AI-assisted)
├── caption_writer.py      # Caption generation
├── postly_client.py       # Postly.ai API integration
├── logger.py              # Logging and persistence
└── requirements.txt
```

---

## 4) RSS Sources (English, Reputable)
- https://rss.nytimes.com/services/xml/rss/nyt/Health.xml
- https://www.medicalnewstoday.com/rss
- https://www.sciencedaily.com/rss/health_medicine.xml
- https://www.cdc.gov/media/rss.xml
- https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml
- https://www.nih.gov/feed
- https://www.health.com/feed

Rules:
- Deduplicate by title + URL
- Process newest first
- Continue until a valid post is produced

---

## 5) AP Herb Product Catalog Ingestion
**Source of truth**: `Product_Info.csv`

**Extract fields**:
- product_name
- product_url
- description
- key_ingredients
- category / sub_category
- tags
- image_path (Dropbox folder per product)

**Image handling**:
- Use Dropbox API to list files inside `image_path`
- Pick the first image file and create a shared link

**Failure fallback**:
- If CSV is empty, skip posting and log failure
- If Dropbox image lookup fails, log missing image URL

---

## 6) Safety Filter (AI-Assisted Hybrid)
**Hard block (code)**:
- pregnancy
- children
- cancer
- diabetes
- mental health
- sexual health

**AI classifier** (OpenAI):
Prompt the model to label:
- `safe` or `unsafe`
- reasons (medical advice? treatment claims? promotional?)

**Decision**:
- If hard-block matched → reject
- Else if AI says `unsafe` → reject
- Else → pass

---

## 7) Product Matching (AI-Assisted Hybrid)
**Baseline scoring**:
- Extract keywords from article
- Score products by ingredient overlap + description similarity + category relevance

**AI ranking (optional)**:
- Provide top 5 candidates + article
- Ask AI to select **exactly one** best match or “no good match”

**Decision**:
- If no product meets threshold → skip article
- Else select top product

---

## 8) Caption Rules (OpenAI)
**Required structure**:
1) Hook (1 sentence)
2) Summary (2–3 sentences)
3) Why it matters (1 sentence)
4) Product tie-in (1–2 sentences, educational only)
5) Source line: `Source: Publisher, Month Day, Year`
6) Product link
7) 8 hashtags

**Constraints**:
- 100–150 words
- English only
- No medical advice or cure/treatment claims

---

## 9) Product Image Handling
1. Resolve product image via Dropbox folder path (`image_path`)
2. Pick first image file and generate shared link
3. Attach shared link via Postly API

---

## 10) Postly.ai Publishing
**Endpoint**: `POST https://openapi.postly.ai/v1/posts`

**Auth**:
- `X-API-KEY: <api-key>`

**Payload essentials**:
- `text`: caption
- `media`: [{ url, type }]
- `target_platforms`: Instagram
- `one_off_schedule`: date + time + timezone (5:00 AM local)

We will align the payload with Postly docs and your provided cURL example.

---

## 11) Logging & Tracking (SQLite + Google Sheets)
Each run logs to **SQLite** and also appends a row to **Google Sheets**:
- timestamp
- rss source
- article title + URL
- product name + URL + image
- caption text
- status (posted/skipped/failed)
- failure reason (if any)

**Google Sheets**: use a service account + `gspread` (or Google Sheets API) and store
credentials in Replit Secrets (e.g., `GOOGLE_SHEETS_CREDENTIALS_JSON`, `GOOGLE_SHEET_ID`).

---

## 12) Scheduling in Replit
**Option A (recommended)**:
- expose `/run_daily` endpoint
- trigger via external cron at 5:00 AM

**Option B**:
- internal scheduler loop (less reliable)

---

## 13) Secrets (Replit Secrets)
- `OPENAI_API_KEY`
- `POSTLY_API_KEY`
- `POSTLY_BASE_URL` (optional, default to `https://openapi.postly.ai`)
- `POSTLY_WORKSPACE` or any required workspace ID
- `DROPBOX_ACCESS_TOKEN`
- `PRODUCT_INFO_CSV_PATH`

---

## 14) Implementation Order (Student-Friendly)
1. AP Herb CSV loader + Dropbox images
2. RSS ingestion
3. Safety filter (AI-assisted)
4. AI caption writer
5. Product matcher (AI-assisted)
6. Postly publishing
7. Logging + schedule trigger

---

## 15) Next Step
If this plan looks good, ask me to **toggle to Act mode**, and I will generate the full Replit-ready codebase (starting with `requirements.txt`).
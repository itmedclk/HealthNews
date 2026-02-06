# Debug & Fix Prompt (HealthNews Automation)

Use this file as a **standard prompt** whenever errors occur in this project. The AI must read this file before proposing any fix.

---

## 1) Project Context (from plan.md)
**Goal**: A Python 3.11+ automation that posts **daily health news** to Instagram at **5:00 AM local time** using **AP Herb** product data and **Postly.ai**.

**Daily Flow**:
1. RSS ingest (dedupe, newest-first)
2. Safety filter (hard block + AI classifier)
3. Caption writer (100–150 words, IG format)
4. AP Herb catalog scrape + cache
5. Product matcher (keyword + AI optional)
6. Postly publish (scheduled 5:00 AM)
7. Logging (SQLite + Google Sheets)

**Constraints**:
- Use OpenAI for AI tasks
- Only AP Herb products
- Avoid unsafe topics and medical claims
- Post via `POST https://openapi.postly.ai/v1/posts`
- Secrets stored in Replit Secrets

**Target File Structure**:
```
main.py
config.py
rss_ingest.py
catalog_service.py
safety_filter.py
matcher.py
caption_writer.py
postly_client.py
logger.py
requirements.txt
```

---

## 2) When to Use This Prompt
Use this prompt when:
- Runtime errors or tracebacks occur
- API requests fail (OpenAI, Postly, RSS, AP Herb)
- Outputs violate constraints (word count, unsafe content, missing fields)
- Automation fails to schedule or post
- Logging or caching fails

---

## 3) Required Inputs (must request if missing)
**Always request/confirm**:
- Full error message/traceback
- The file name(s) and code block(s) involved
- Recent changes (if any)
- Relevant config/env vars (redact secrets)
- Sample inputs (RSS item, product entry, caption output)
- Logs from SQLite/Google Sheets if logging failed

If any of these are missing, **ask for them before proposing fixes**.

---

## 4) Debug Workflow (AI must follow)
1. **Classify the failure**: runtime error, API error, data mismatch, safety violation, scheduling issue, or logging issue.
2. **Identify root cause** using traceback + context (line number, function, missing key, bad response, etc.).
3. **Validate assumptions** against constraints and plan rules.
4. **Propose minimal fix** consistent with architecture and file structure.
5. **Check side effects** (does it affect other modules, safety, or scheduling?).
6. **Add/adjust logging** if it improves diagnosability.

---

## 5) Common Failure Modes & Guidance
**RSS Ingest**:
- Empty feed → check URL, network, parse errors
- Dedupe bug → verify title+URL uniqueness

**AP Herb Catalog**:
- Scrape failure → use cached JSON/SQLite fallback
- Missing fields → guard with defaults

**Safety Filter**:
- Unsafe topic slipped → add to hard block list or classifier rules
- False positive → adjust classifier prompt or thresholds

**Caption Writer**:
- Wrong length → enforce word count post-process
- Missing required sections → validate structure and regenerate

**Postly API**:
- 4xx/5xx → log response body + verify payload schema
- Image failure → validate URL format and content type

**Logging**:
- SQLite locked → ensure connections are closed
- Sheets API error → verify credentials and permissions

---

## 6) Output Format (AI must follow)
**Return your fix in this structure**:
1. **Root Cause Summary** (1–3 sentences)
2. **Proposed Fix** (bulleted list)
3. **Files to Change** (with exact paths)
4. **Patch or Code Snippets** (minimal diffs)
5. **Verification Steps** (how to confirm the fix)

---

## 7) Do NOT Do
- Do not add medical advice or treatment claims
- Do not introduce new dependencies unless necessary
- Do not bypass safety filtering
- Do not change scheduling time without explicit request

---

## 8) Quick Checklist (before final answer)
- [ ] Did I request all missing required inputs?
- [ ] Did I identify the exact root cause?
- [ ] Is the fix minimal and aligned to plan.md?
- [ ] Did I include the required output format?
- [ ] Did I avoid unsafe or noncompliant changes?

from datetime import datetime
from typing import Dict, List

import feedparser


# Retrieve RSS data from all sources and normalize into entry dictionaries.
def fetch_rss_entries(sources: List[str]) -> List[Dict]:
    """Download RSS feeds and normalize them into a list of entry dictionaries."""
    entries: List[Dict] = []
    for source in sources:
        feed = feedparser.parse(source)
        for entry in feed.entries:
            published = None
            if entry.get("published_parsed"):
                published = datetime(*entry.published_parsed[:6])
            entries.append(
                {
                    "source": source,
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": published,
                }
            )
    return entries


# Remove duplicate RSS entries based on title + URL.
def dedupe_entries(entries: List[Dict]) -> List[Dict]:
    """Remove duplicate entries based on title + URL keys."""
    seen = set()
    unique_entries = []
    for entry in entries:
        key = (entry.get("title", "").strip().lower(), entry.get("url", "").strip())
        if key in seen:
            continue
        seen.add(key)
        unique_entries.append(entry)
    return unique_entries


# Sort RSS entries so newest items are processed first.
def sort_entries_newest(entries: List[Dict]) -> List[Dict]:
    """Sort entries so the most recent items come first."""
    return sorted(entries, key=lambda e: e.get("published") or datetime.min, reverse=True)


# Orchestrate fetching, deduping, and sorting of RSS entries.
def ingest_rss(sources: List[str]) -> List[Dict]:
    """Fetch, dedupe, and sort RSS entries from all configured sources."""
    entries = fetch_rss_entries(sources)
    entries = dedupe_entries(entries)
    return sort_entries_newest(entries)

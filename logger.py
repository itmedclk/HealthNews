import json
import os
import sqlite3
from datetime import datetime
from typing import Dict


# Ensure the directory for a file path exists.
def _ensure_dir(path: str) -> None:
    """Create parent directories for a file path if they don't exist."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


# Create the logs table in SQLite if it doesn't already exist.
def init_db(sqlite_path: str) -> None:
    """Initialize the SQLite database and logs table if missing."""
    _ensure_dir(sqlite_path)
    with sqlite3.connect(sqlite_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                rss_source TEXT,
                article_title TEXT,
                article_url TEXT,
                product_name TEXT,
                product_url TEXT,
                product_image_url TEXT,
                caption TEXT,
                status TEXT,
                reason TEXT
            )
            """
        )
        conn.commit()


# Insert a log record into SQLite.
def log_event(sqlite_path: str, payload: Dict) -> None:
    """Insert a log payload into the SQLite logs table."""
    _ensure_dir(sqlite_path)
    with sqlite3.connect(sqlite_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO logs (
                timestamp,
                rss_source,
                article_title,
                article_url,
                product_name,
                product_url,
                product_image_url,
                caption,
                status,
                reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("timestamp"),
                payload.get("rss_source"),
                payload.get("article_title"),
                payload.get("article_url"),
                payload.get("product_name"),
                payload.get("product_url"),
                payload.get("product_image_url"),
                payload.get("caption"),
                payload.get("status"),
                payload.get("reason"),
            ),
        )
        conn.commit()


# Build a normalized log payload from pipeline data.
def build_log_payload(entry: Dict, product: Dict, caption: str, status: str, reason: str = "") -> Dict:
    """Build a normalized log dictionary for persistence and reporting."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "rss_source": entry.get("source", ""),
        "article_title": entry.get("title", ""),
        "article_url": entry.get("url", ""),
        "product_name": product.get("product_name", ""),
        "product_url": product.get("product_url", ""),
        "product_image_url": product.get("product_image_url", ""),
        "caption": caption,
        "status": status,
        "reason": reason,
    }


# Append a log row to Google Sheets when configured.
def append_sheet_log(credentials_json: str, sheet_id: str, payload: Dict) -> None:
    """Append a log row to Google Sheets when credentials are provided."""
    if not credentials_json or not sheet_id:
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        info = json.loads(credentials_json)
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(sheet_id).sheet1
        sheet.append_row(
            [
                payload.get("timestamp"),
                payload.get("rss_source"),
                payload.get("article_title"),
                payload.get("article_url"),
                payload.get("product_name"),
                payload.get("product_url"),
                payload.get("product_image_url"),
                payload.get("caption"),
                payload.get("status"),
                payload.get("reason"),
            ]
        )
    except Exception:
        return

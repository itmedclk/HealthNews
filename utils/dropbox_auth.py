import os
import time
from typing import Optional

import requests


_token_cache = {"token": None, "expires_at": 0}


def get_dropbox_access_token(force_refresh: bool = False) -> Optional[str]:
    """Fetch and cache a Dropbox access token using refresh token credentials."""
    cached = _token_cache.get("token")
    if not force_refresh and cached and time.time() < _token_cache.get("expires_at", 0):
        return cached

    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN", "")
    client_id = os.getenv("DROPBOX_CLIENT_ID", "")
    client_secret = os.getenv("DROPBOX_CLIENT_SECRET", "")
    if not refresh_token or not client_id or not client_secret:
        return None

    resp = requests.post(
        "https://api.dropboxapi.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(
            f"Dropbox refresh token failed ({resp.status_code}): {resp.text}"
        )
    data = resp.json()

    _token_cache["token"] = data.get("access_token")
    _token_cache["expires_at"] = time.time() + int(data.get("expires_in", 0)) - 60
    return _token_cache["token"]
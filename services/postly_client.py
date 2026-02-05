from typing import Dict

import requests


# Send a scheduled Instagram post to Postly's API.
def create_post(
    base_url: str,
    api_key: str,
    caption: str,
    image_url: str,
    scheduled_iso: str,
    target_platforms: str = "",
    workspace_ids: str = "",
) -> Dict:
    """Send a scheduled Instagram post request to the Postly API."""
    endpoint = f"{base_url.rstrip('/')}/v1/posts"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "text": caption,
        "media": [{"url": image_url, "type": "image"}],
        "one_off_schedule": scheduled_iso,
    }
    if target_platforms:
        payload["target_platforms"] = target_platforms
    if workspace_ids:
        payload["workspace"] = workspace_ids
    response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

import csv
import json
import os
from typing import Dict, List, Optional

import requests

from utils.config import SETTINGS
from utils.dropbox_auth import get_dropbox_access_token


ROTATION_STATE_PATH = "data/image_rotation.json"


def _is_image_file(name: str) -> bool:
    """Check if a filename looks like a supported image type."""
    return name.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))


def _list_dropbox_files(folder_path: str) -> List[Dict]:
    """List files in a Dropbox folder using the API."""
    access_token = SETTINGS.dropbox_access_token or get_dropbox_access_token()
    if not access_token:
        return []
    url = "https://api.dropboxapi.com/2/files/list_folder"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json={"path": folder_path}, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Dropbox list_folder failed ({response.status_code}): {response.text}")
    return response.json().get("entries", [])


def _create_dropbox_shared_link(path: str) -> Optional[str]:
    """Create a shared link for a Dropbox file and return a direct-download URL."""
    access_token = SETTINGS.dropbox_access_token or get_dropbox_access_token()
    if not access_token:
        return None
    url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json={"path": path}, timeout=30)
    if response.status_code == 409:
        # If link exists already, fetch it instead.
        list_url = "https://api.dropboxapi.com/2/sharing/list_shared_links"
        list_response = requests.post(list_url, headers=headers, json={"path": path, "direct_only": True}, timeout=30)
        if list_response.status_code >= 400:
            raise RuntimeError(
                f"Dropbox list_shared_links failed ({list_response.status_code}): {list_response.text}"
            )
        links = list_response.json().get("links", [])
        if not links:
            return None
        shared_url = links[0].get("url")
    else:
        if response.status_code >= 400:
            raise RuntimeError(
                f"Dropbox create_shared_link failed ({response.status_code}): {response.text}"
            )
        shared_url = response.json().get("url")
    if not shared_url:
        return None
    return shared_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")


def _load_rotation_state() -> Dict[str, int]:
    """Load rotation state from disk (per image_path)."""
    if not os.path.exists(ROTATION_STATE_PATH):
        return {}
    try:
        with open(ROTATION_STATE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, dict):
                return {str(k): int(v) for k, v in data.items()}
    except Exception:
        return {}
    return {}


def _save_rotation_state(state: Dict[str, int]) -> None:
    """Persist rotation state to disk."""
    os.makedirs(os.path.dirname(ROTATION_STATE_PATH), exist_ok=True)
    with open(ROTATION_STATE_PATH, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def _resolve_dropbox_image(folder_path: str) -> Dict[str, str]:
    """Pick the next image in rotation and return URL + status info."""
    if not (SETTINGS.dropbox_access_token or get_dropbox_access_token()):
        return {"image_url": "", "status": "missing_dropbox_token"}
    if not folder_path:
        return {"image_url": "", "status": "missing_image_path"}
    entries = _list_dropbox_files(folder_path)
    if not entries:
        return {"image_url": "", "status": "no_files_found"}
    image_files = [
        entry
        for entry in entries
        if entry.get(".tag") == "file" and _is_image_file(entry.get("name", ""))
    ]
    if not image_files:
        return {"image_url": "", "status": "no_image_files"}
    image_files.sort(key=lambda entry: entry.get("name", ""))
    rotation_state = _load_rotation_state()
    current_index = rotation_state.get(folder_path, -1)
    next_index = (current_index + 1) % len(image_files)
    chosen = image_files[next_index]
    link = _create_dropbox_shared_link(chosen.get("path_lower") or chosen.get("path_display"))
    if link:
        rotation_state[folder_path] = next_index
        _save_rotation_state(rotation_state)
        return {
            "image_url": link,
            "status": "ok",
            "image_name": chosen.get("name", ""),
            "rotation_index": str(next_index + 1),
            "rotation_total": str(len(image_files)),
        }
    return {"image_url": "", "status": "link_create_failed"}


# Load product data from CSV and resolve Dropbox image links.
def load_products_from_csv(csv_path: str, resolve_images: bool = True) -> List[Dict]:
    """Read product data from CSV and attach Dropbox image URLs when enabled."""
    if not os.path.exists(csv_path):
        info_path = os.path.join("info", csv_path)
        if os.path.exists(info_path):
            csv_path = info_path
    products: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row.get("is_active", "")).strip() != "1":
                continue
            image_path = (row.get("image_path") or "").strip()
            image_result = _resolve_dropbox_image(image_path) if resolve_images else {"image_url": ""}
            product = {
                "product_name": row.get("product_name", "").strip(),
                "product_url": row.get("product_url", "").strip(),
                "product_image_url": image_result.get("image_url", ""),
                "image_path": image_path,
                "image_status": image_result.get("status", "unknown"),
                "image_name": image_result.get("image_name", ""),
                "image_rotation_index": image_result.get("rotation_index", ""),
                "image_rotation_total": image_result.get("rotation_total", ""),
                "description": row.get("description", "").strip(),
                "ingredients": row.get("key_ingredients", "").strip(),
                "main_benefit": row.get("main_benefit", "").strip(),
                "category": row.get("category", "").strip(),
                "sub_category": row.get("sub_category", "").strip(),
                "tags": row.get("tags", "").strip(),
                "priority": row.get("priority", "").strip(),
            }
            products.append(product)
    return products


def load_brands_from_csv(csv_path: str) -> List[Dict]:
    """Read brand metadata from CSV (brand_name, product_info_csv_path, target_platforms, workspace_ids, tags)."""
    if not os.path.exists(csv_path):
        info_path = os.path.join("info", csv_path)
        if os.path.exists(info_path):
            csv_path = info_path
    brands: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            brand_name = (row.get("brand_name") or "").strip()
            if not brand_name:
                continue
            brands.append(
                {
                    "brand_name": brand_name,
                    "product_info_csv_path": (row.get("product_info_csv_path") or "").strip(),
                    "target_platforms": (row.get("target_platforms") or "").strip(),
                    "workspace_ids": (row.get("workspace_ids") or "").strip(),
                    "rss_sources": (row.get("rss_sources") or "").strip(),
                    "tags": (row.get("tags") or "").strip(),
                }
            )
    return brands


def _split_csv_list(value: str) -> List[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def derive_brand_topics(products: List[Dict]) -> Dict[str, str]:
    """Derive topics for a brand based on its product catalog fields."""
    categories = sorted({p.get("category", "").strip() for p in products if p.get("category")})
    subcategories = sorted({p.get("sub_category", "").strip() for p in products if p.get("sub_category")})
    tag_set = set()
    for product in products:
        tags = product.get("tags", "") or ""
        for tag in tags.split(","):
            cleaned = tag.strip()
            if cleaned:
                tag_set.add(cleaned)
    tags = sorted(tag_set)
    topics = sorted({*categories, *subcategories, *tags})
    return {
        "topics": ", ".join(topics),
        "product_categories": ", ".join(categories),
        "product_subcategories": ", ".join(subcategories),
        "product_tags": ", ".join(tags),
    }


def parse_brand_rss_sources(raw_sources: str) -> List[str]:
    """Parse a pipe-delimited list of RSS sources for a brand (optional override)."""
    return _split_csv_list(raw_sources)

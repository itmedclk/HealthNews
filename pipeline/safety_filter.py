from typing import Dict, List, Tuple

from utils.config import SETTINGS
from openai import OpenAI


# Check for hard-blocked topics (returns False if found).
def hard_block_check(text: str) -> Tuple[bool, str]:
    """Return False with a reason if hard-blocked topics appear in the text."""
    lowered = text.lower()
    for topic in SETTINGS.hard_block_topics:
        if topic in lowered:
            return False, f"Hard-blocked topic detected: {topic}"
    return True, ""


# Placeholder AI safety check .
def _build_client() -> OpenAI:
    return OpenAI(api_key=SETTINGS.novita_api_key, base_url=SETTINGS.novita_base_url)


def ai_hardblock_check(text: str) -> Tuple[bool, str]:
    """Use NovitaAI to flag hard-block topics in the article."""
    if not SETTINGS.novita_api_key:
        return False, "Missing NOVITA_API_KEY for AI hard-block check"

    prompt = (
        "You are a safety classifier. Determine if the article discusses any hard-block topics "
        "(pregnancy, children, cancer, diabetes, mental health, sexual health). "
        "Reply with a single line in the format: HARDBLOCK=yes|no;REASON=...\n\n"
        f"ARTICLE:\n{text}"
    )

    client = _build_client()
    response = client.chat.completions.create(
        model=SETTINGS.novita_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = response.choices[0].message.content.strip()
    if content.lower().startswith("hardblock=yes"):
        return False, content
    return True, ""


def ai_product_relevance_check(text: str, products: List[Dict]) -> Tuple[bool, str, float]:
    """Use NovitaAI to decide if the article relates to any products in the catalog."""
    if not SETTINGS.novita_api_key:
        return False, "Missing NOVITA_API_KEY for AI relevance check", 0.0

    product_summaries = []
    for product in products[:30]:
        summary = " | ".join(
            [
                product.get("product_name", ""),
                product.get("category", ""),
                product.get("main_benefit", ""),
                product.get("ingredients", ""),
                product.get("tags", ""),
            ]
        )
        product_summaries.append(summary.strip(" |"))

    prompt = (
        "You are a relevance classifier for a health news Instagram automation. "
        "Given a news article and a list of products, decide whether the article is "
        "related to at least one product. Return a relevance score between 0 and 1. "
        "Reply with a single line in the format: RELATED=yes|no;SCORE=0.00;REASON=...\n\n"
        f"ARTICLE:\n{text}\n\n"
        "PRODUCTS:\n- "
        + "\n- ".join(product_summaries)
    )

    client = _build_client()
    response = client.chat.completions.create(
        model=SETTINGS.novita_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = response.choices[0].message.content.strip()
    lowered = content.lower()
    score = 0.0
    if "score=" in lowered:
        try:
            score_str = lowered.split("score=")[1].split(";")[0].strip()
            score = float(score_str)
        except ValueError:
            score = 0.0
    if lowered.startswith("related=yes") and score >= SETTINGS.relevance_threshold:
        return True, "", score
    return False, content, score


# Run both hard-block and AI safety checks on a single entry.
def safety_filter(entry: Dict, products: List[Dict]) -> Tuple[bool, str]:
    """Combine hard-block and AI checks to decide if an entry is safe to post."""
    combined = f"{entry.get('title', '')} {entry.get('summary', '')}"
    ok, reason = hard_block_check(combined)
    if not ok:
        return False, reason
    ok, reason = ai_hardblock_check(combined)
    if not ok:
        return False, reason
    ok, reason, _score = ai_product_relevance_check(combined, products)
    if not ok:
        return False, reason
    return True, ""

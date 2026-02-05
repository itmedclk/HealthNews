from datetime import datetime
from typing import Dict

from openai import OpenAI
from utils.config import SETTINGS


# -------------------------
# Helpers
# -------------------------

def _count_words(text: str) -> int:
    return len(text.split())


def _format_source(entry: Dict) -> str:
    published = entry.get("published")
    if isinstance(published, datetime):
        date_str = published.strftime("%B %d, %Y")
    else:
        date_str = datetime.utcnow().strftime("%B %d, %Y")

    source_url = entry.get("url") or entry.get("source") or "Unknown"
    return f"Source: {source_url}, {date_str}"


def _build_caption_prompt(entry: Dict, product: Dict) -> str:
    """
    Build a strict but natural prompt for Instagram caption generation.
    """
    return f"""
You are writing an educational Instagram caption for a health brand.

GOAL:
- Introduce today’s health news clearly and naturally
- Explain why it matters in everyday terms
- Make a smooth, non-promotional connection to a related wellness product

STRICT RULES:
- 100–150 words total
- English only
- Educational tone ONLY
- No medical advice
- No disease treatment or cure claims
- No guarantees or exaggerated benefits
- Do NOT sound like an advertisement

STYLE:
- Friendly, informative, calm
- Natural transitions (e.g. “this is why…”, “in this context…”, “that’s where…”)
- Neutral, trustworthy voice

STRUCTURE (follow in order, do NOT label sections):
1) Introduce today’s health news based on the article
2) Briefly explain why it matters for everyday health
3) Naturally connect the topic to a related wellness product (educational only)
4) A line starting with exactly: Learn more:
   followed by the product URL
5) A line starting with exactly: Source:
   followed by the article URL and date
6) End with exactly 8 relevant hashtags

ARTICLE:
Title: {entry.get("title", "")}
Summary: {entry.get("summary", "")}

PRODUCT:
Name: {product.get("product_name", "")}
Description: {product.get("description", "")}
Key Ingredients: {product.get("key_ingredients", "")}
Product URL: {product.get("product_url", "")}

Write the caption now.
""".strip()


# -------------------------
# Main caption generator
# -------------------------

def generate_caption(entry: Dict, product: Dict) -> str:
    """
    Generate an Instagram-ready caption using OpenAI,
    then enforce length and formatting constraints.
    """
    client = OpenAI(api_key=SETTINGS.novita_api_key, base_url=SETTINGS.novita_base_url)

    prompt = _build_caption_prompt(entry, product)

    response = client.chat.completions.create(
        model=SETTINGS.novita_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    caption = response.choices[0].message.content.strip()

    # --- Safety net: word count enforcement ---
    word_count = _count_words(caption)

    if word_count < SETTINGS.caption_min_words:
        caption += " This content is shared for educational purposes only."
    elif word_count > SETTINGS.caption_max_words:
        caption = " ".join(caption.split()[: SETTINGS.caption_max_words])

    return caption

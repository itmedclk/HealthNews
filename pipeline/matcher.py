import re
from typing import Dict, List, Tuple

from openai import OpenAI

from utils.config import SETTINGS


# Tokenize text into keywords for similarity scoring.
def _tokenize(text: str) -> List[str]:
    """Extract lowercase tokens for simple keyword matching."""
    return re.findall(r"[a-zA-Z]{3,}", text.lower())


# Score how well a product matches a news entry.
def score_product(entry: Dict, product: Dict) -> float:
    """Compute a similarity score between a news entry and a product description."""
    text = f"{entry.get('title', '')} {entry.get('summary', '')}"
    tokens = set(_tokenize(text))
    if not tokens:
        return 0.0
    description = " ".join(
        [
            product.get("product_name", ""),
            product.get("description", ""),
            product.get("ingredients", ""),
            product.get("category", ""),
        ]
    )
    product_tokens = set(_tokenize(description))
    if not product_tokens:
        return 0.0
    overlap = tokens.intersection(product_tokens)
    return len(overlap) / max(len(tokens), 1)


# Select the top matching product above the minimum score threshold.
def _rank_by_keywords(entry: Dict, products: List[Dict]) -> List[Tuple[Dict, float]]:
    """Return products sorted by keyword overlap score (desc)."""
    scored: List[Tuple[Dict, float]] = []
    for product in products:
        scored.append((product, score_product(entry, product)))
    return sorted(scored, key=lambda item: item[1], reverse=True)


def _ai_rerank(entry: Dict, candidates: List[Tuple[Dict, float]]) -> Tuple[Dict, float]:
    """Use NovitaAI to select the best product from the top candidates."""
    if not SETTINGS.novita_api_key:
        return {}, 0.0

    prompt_lines = []
    for idx, (product, score) in enumerate(candidates, start=1):
        prompt_lines.append(
            f"{idx}) {product.get('product_name', '')} | {product.get('category', '')} | "
            f"{product.get('main_benefit', '')} | score={score:.2f}"
        )

    prompt = (
        "You are selecting the most relevant AP Herb product for a health news article. "
        "Choose the best option number from the list, or reply NONE if nothing fits. "
        "Reply with: CHOICE=<number or NONE>\n\n"
        f"ARTICLE:\n{entry.get('title', '')} {entry.get('summary', '')}\n\n"
        "CANDIDATES:\n" + "\n".join(prompt_lines)
    )

    client = OpenAI(api_key=SETTINGS.novita_api_key, base_url=SETTINGS.novita_base_url)
    response = client.chat.completions.create(
        model=SETTINGS.novita_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = response.choices[0].message.content.strip().lower()
    if "choice=none" in content:
        return {}, 0.0
    if "choice=" in content:
        try:
            value = content.split("choice=")[1].split()[0].strip()
            index = int(value)
            if 1 <= index <= len(candidates):
                return candidates[index - 1]
        except ValueError:
            return {}, 0.0
    return {}, 0.0


def select_best_product(entry: Dict, products: List[Dict], min_score: float = 0.05) -> Tuple[Dict, float]:
    """Pick the best product match if it meets the minimum similarity score."""
    ranked = _rank_by_keywords(entry, products)
    if not ranked:
        return {}, 0.0
    top_ranked = [item for item in ranked if item[1] > 0][: SETTINGS.ai_rerank_top_n]
    if SETTINGS.use_ai_rerank and top_ranked:
        product, score = _ai_rerank(entry, top_ranked)
        if product and score >= min_score:
            return product, score
        return {}, score

    best_product, best_score = ranked[0]
    if best_score < min_score:
        return {}, best_score
    return best_product, best_score

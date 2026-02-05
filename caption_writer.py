from datetime import datetime
from typing import Dict

from config import SETTINGS


# Count words in a caption for length enforcement.
def _count_words(text: str) -> int:
    """Count words in a caption string."""
    return len(text.split())


# Format the source line with publisher name and date.
def _format_source(entry: Dict) -> str:
    """Format the source line with article URL (or RSS source) and published date."""
    published = entry.get("published")
    if isinstance(published, datetime):
        date_str = published.strftime("%B %d, %Y")
    else:
        date_str = datetime.utcnow().strftime("%B %d, %Y")
    source_url = entry.get("url") or entry.get("source") or "Unknown"
    return f"Source: {source_url}, {date_str}"


# Build the Instagram caption with hook, summary, product tie-in, and hashtags.
def generate_caption(entry: Dict, product: Dict) -> str:
    """Assemble an Instagram-ready caption that meets length and formatting rules."""
    hook = f"{entry.get('title', 'Today in health news')}."
    summary = entry.get("summary", "").strip()
    summary_sentence = summary if summary.endswith(".") else f"{summary}."
    why = "Why it matters: understanding health trends helps inform daily wellness choices."
    product_line = (
        f"Learn more about {product.get('product_name', 'this AP Herb product')} "
        "as part of a balanced, educational wellness routine."
    )
    source = _format_source(entry)
    product_link = product.get("product_url", "")
    hashtags = "#health #wellness #nutrition #wellbeing #fitness #healthyhabits #selfcare #healthnews"

    caption = "\n".join(
        [
            hook,
            summary_sentence,
            why,
            product_line,
            source,
            product_link,
            hashtags,
        ]
    ).strip()

    word_count = _count_words(caption)
    if word_count < SETTINGS.caption_min_words:
        padding = " This update is shared for educational purposes only."
        while _count_words(caption) < SETTINGS.caption_min_words:
            caption += padding
    elif word_count > SETTINGS.caption_max_words:
        words = caption.split()
        caption = " ".join(words[: SETTINGS.caption_max_words])
    return caption

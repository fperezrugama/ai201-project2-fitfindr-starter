"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    stop_words = {
        "a",
        "an",
        "and",
        "for",
        "in",
        "of",
        "the",
        "to",
        "with",
    }

    def normalize(value) -> str:
        return str(value or "").lower()

    def tokenize(value) -> list[str]:
        return re.findall(r"[a-z0-9]+", normalize(value))

    def list_text(value) -> str:
        if isinstance(value, list):
            return " ".join(str(item) for item in value)
        return str(value or "")

    def size_matches(requested_size: str | None, listing_size) -> bool:
        if not requested_size or not str(requested_size).strip():
            return True

        requested_tokens = set(tokenize(requested_size))
        listing_tokens = set(tokenize(listing_size))
        if not requested_tokens or not listing_tokens:
            return False

        def canonical_sizes(value) -> set[str]:
            value_text = normalize(value).replace("-", " ")
            tokens = set(tokenize(value_text))
            phrase_matches = set()
            if re.search(r"\b(extra|x)\s*small\b", value_text):
                phrase_matches.add("xs")
            if re.search(r"\b(extra|x)\s*large\b", value_text):
                phrase_matches.add("xl")
            if phrase_matches:
                return phrase_matches

            token_map = {
                "xs": "xs",
                "xsmall": "xs",
                "s": "s",
                "small": "s",
                "m": "m",
                "medium": "m",
                "med": "m",
                "l": "l",
                "large": "l",
                "xl": "xl",
                "xlarge": "xl",
                "xxl": "xxl",
                "2xl": "xxl",
                "xxlarge": "xxl",
            }
            return {
                token_map[token]
                for token in tokens
                if token in token_map
            }

        requested_canonical_sizes = canonical_sizes(requested_size)
        listing_canonical_sizes = canonical_sizes(listing_size)
        if requested_canonical_sizes and listing_canonical_sizes:
            return bool(requested_canonical_sizes & listing_canonical_sizes)

        if requested_tokens <= listing_tokens:
            return True

        requested_digits = set(re.findall(r"\d+", normalize(requested_size)))
        listing_digits = set(re.findall(r"\d+", normalize(listing_size)))
        return bool(requested_digits and requested_digits <= listing_digits)

    try:
        listings = load_listings()
    except Exception:
        return []

    if not isinstance(listings, list):
        return []

    query = normalize(description)
    query_terms = {
        term for term in tokenize(description) if term not in stop_words
    }
    if not query_terms:
        return []

    try:
        price_limit = float(max_price) if max_price is not None else None
    except (TypeError, ValueError):
        return []

    scored_listings = []
    for listing in listings:
        try:
            price = float(listing.get("price", 0))
        except (TypeError, ValueError, AttributeError):
            price = float("inf")

        if price_limit is not None and price > price_limit:
            continue

        if not size_matches(size, listing.get("size")):
            continue

        title = normalize(listing.get("title"))
        item_description = normalize(listing.get("description"))
        category = normalize(listing.get("category"))
        style_tags = normalize(list_text(listing.get("style_tags")))
        colors = normalize(list_text(listing.get("colors")))
        brand = normalize(listing.get("brand"))

        title_tokens = set(tokenize(title))
        description_tokens = set(tokenize(item_description))
        metadata_tokens = set(
            tokenize(" ".join([category, style_tags, colors, brand]))
        )

        score = 0
        if query in title:
            score += 8
        if query in item_description:
            score += 5
        if query in " ".join([category, style_tags, colors, brand]):
            score += 4

        for term in query_terms:
            if term in title_tokens:
                score += 3
            if term in description_tokens:
                score += 2
            if term in metadata_tokens:
                score += 2

        if query_terms <= (title_tokens | description_tokens | metadata_tokens):
            score += 3

        if score > 0:
            scored_listings.append((score, price, listing))

    scored_listings.sort(
        key=lambda match: (
            -match[0],
            match[1],
            normalize(match[2].get("title")),
        )
    )
    return [listing for _, _, listing in scored_listings]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    return ""


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    return ""

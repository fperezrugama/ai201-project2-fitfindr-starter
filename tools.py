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

import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


_STYLE_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "style_profile.json",
)
_DEFAULT_STYLE_PROFILE = {
    "favorite_styles": [],
    "preferred_colors": [],
    "fit_preferences": [],
}


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Style profile memory helpers ──────────────────────────────────────────────

def load_style_profile() -> dict:
    """Load saved style preferences, or return an empty profile if missing."""
    if not os.path.exists(_STYLE_PROFILE_PATH):
        return {key: value.copy() for key, value in _DEFAULT_STYLE_PROFILE.items()}

    with open(_STYLE_PROFILE_PATH, "r", encoding="utf-8") as profile_file:
        profile = json.load(profile_file)

    if not isinstance(profile, dict):
        raise ValueError("Style profile must be a dictionary.")

    normalized_profile = {}
    for key, default_value in _DEFAULT_STYLE_PROFILE.items():
        value = profile.get(key, default_value)
        normalized_profile[key] = value if isinstance(value, list) else []

    return normalized_profile


def save_style_profile(profile: dict) -> None:
    """Save style preferences to the project data directory."""
    if not isinstance(profile, dict):
        raise ValueError("Style profile must be a dictionary.")

    normalized_profile = {}
    for key, default_value in _DEFAULT_STYLE_PROFILE.items():
        value = profile.get(key, default_value)
        normalized_profile[key] = value if isinstance(value, list) else []

    with open(_STYLE_PROFILE_PATH, "w", encoding="utf-8") as profile_file:
        json.dump(normalized_profile, profile_file, indent=2)
        profile_file.write("\n")


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
        "find",
        "in",
        "like",
        "looking",
        "need",
        "of",
        "some",
        "the",
        "to",
        "want",
        "with",
    }
    weak_style_terms = {
        "2000s",
        "90s",
        "classic",
        "retro",
        "streetwear",
        "vintage",
        "y2k",
    }

    def normalize(value) -> str:
        return str(value or "").lower()

    def tokenize(value) -> list[str]:
        return re.findall(r"[a-z0-9]+", normalize(value))

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

    query_tokens = [
        term for term in tokenize(description) if term not in stop_words
    ]
    query_terms = set(query_tokens)
    if not query_terms:
        return []
    query = " ".join(query_tokens)
    query_phrases = {
        " ".join(query_tokens[start:end])
        for start in range(len(query_tokens))
        for end in range(start + 2, len(query_tokens) + 1)
    }
    important_terms = query_terms - weak_style_terms
    requires_strong_match = len(query_terms) > 1

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

        style_tag_values = listing.get("style_tags") or []
        color_values = listing.get("colors") or []
        if not isinstance(style_tag_values, list):
            style_tag_values = [style_tag_values]
        if not isinstance(color_values, list):
            color_values = [color_values]

        title = " ".join(tokenize(listing.get("title")))
        item_description = " ".join(tokenize(listing.get("description")))
        category = " ".join(tokenize(listing.get("category")))
        style_tag_phrases = [
            " ".join(tokenize(tag)) for tag in style_tag_values
        ]
        color_phrases = [
            " ".join(tokenize(color)) for color in color_values
        ]
        brand = " ".join(tokenize(listing.get("brand")))
        style_tags = " ".join(style_tag_phrases)
        colors = " ".join(color_phrases)
        metadata = " ".join([category, style_tags, colors, brand])

        title_tokens = set(tokenize(title))
        description_tokens = set(tokenize(item_description))
        style_tag_tokens = set(tokenize(style_tags))
        metadata_tokens = set(tokenize(metadata))
        all_tokens = title_tokens | description_tokens | metadata_tokens
        matched_terms = query_terms & all_tokens
        multi_word_style_tag_matches = {
            tag for tag in style_tag_phrases
            if len(tokenize(tag)) > 1 and tag in query_phrases
        }

        full_query_in_title = bool(query and query in title)
        full_query_in_description = bool(query and query in item_description)
        full_query_in_style_tags = query in style_tag_phrases
        title_phrase_matches = {
            phrase for phrase in query_phrases if phrase in title
        }
        description_phrase_matches = {
            phrase for phrase in query_phrases if phrase in item_description
        }
        style_tag_phrase_matches = {
            phrase for phrase in query_phrases
            if phrase in style_tag_phrases
        }
        exact_style_tag_matches = (
            style_tag_phrase_matches | multi_word_style_tag_matches
        )
        strong_title_terms = (
            (title_tokens & important_terms)
            if important_terms
            else (title_tokens & query_terms)
        )
        has_all_important_terms = bool(
            important_terms and important_terms <= all_tokens
        )
        has_strong_match = any(
            [
                full_query_in_title,
                full_query_in_description,
                full_query_in_style_tags,
                bool(title_phrase_matches),
                bool(exact_style_tag_matches),
                bool(strong_title_terms),
                has_all_important_terms,
            ]
        )

        if not matched_terms:
            continue
        if requires_strong_match and not has_strong_match:
            continue
        if (
            requires_strong_match
            and important_terms
            and matched_terms <= weak_style_terms
        ):
            continue

        score = 0
        if full_query_in_title:
            score += 60
        if full_query_in_style_tags:
            score += 54
        if full_query_in_description:
            score += 32

        score += len(title_phrase_matches) * 42
        score += len(exact_style_tag_matches) * 38
        score += len(description_phrase_matches) * 16

        if important_terms and important_terms <= title_tokens:
            score += 36
        if important_terms and important_terms <= style_tag_tokens:
            score += 32
        if important_terms and important_terms <= description_tokens:
            score += 12

        for term in query_terms:
            is_important_term = term in important_terms
            if term in title_tokens:
                score += 14 if is_important_term else 1
            if term in style_tag_tokens:
                score += 12 if is_important_term else 1
            if term in description_tokens:
                score += 5 if is_important_term else 0
            if term in metadata_tokens:
                score += 3 if is_important_term else 0

        if has_all_important_terms:
            score += 18
        if query_terms <= all_tokens:
            score += 6

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
    if (
        not isinstance(new_item, dict)
        or not new_item
        or not any(
            new_item.get(field)
            for field in (
                "title",
                "name",
                "category",
                "description",
                "style_tags",
                "colors",
            )
        )
    ):
        return (
            "I can't suggest an outfit because the selected thrift item is "
            "missing or invalid. Please choose a valid listing first."
        )

    def clean_text(value, default: str = "unspecified") -> str:
        if value is None:
            return default
        if isinstance(value, list):
            cleaned_items = [
                str(item).strip() for item in value if str(item).strip()
            ]
            return ", ".join(cleaned_items) if cleaned_items else default
        text = str(value).strip()
        return text if text else default

    def item_name(item: dict) -> str:
        return clean_text(
            item.get("title") or item.get("name") or item.get("category"),
            "the selected thrift item",
        )

    def format_listing(item: dict) -> str:
        details = [
            f"Title: {item_name(item)}",
            f"Category: {clean_text(item.get('category'))}",
            f"Brand: {clean_text(item.get('brand'))}",
            f"Colors: {clean_text(item.get('colors'))}",
            f"Style tags: {clean_text(item.get('style_tags'))}",
            f"Description: {clean_text(item.get('description'))}",
        ]
        if item.get("price") is not None:
            details.append(f"Price: ${item.get('price')}")
        if item.get("platform") is not None:
            details.append(f"Platform: {item.get('platform')}")
        return "\n".join(details)

    def format_wardrobe_item(item: dict) -> str:
        return (
            f"- {item_name(item)} "
            f"({clean_text(item.get('category'))}; "
            f"colors: {clean_text(item.get('colors'))}; "
            f"style: {clean_text(item.get('style_tags'))}; "
            f"notes: {clean_text(item.get('notes'))})"
        )

    def valid_wardrobe_items(wardrobe_data) -> list[dict]:
        if not isinstance(wardrobe_data, dict):
            return []
        items = wardrobe_data.get("items")
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict) and item]

    def format_style_profile(wardrobe_data) -> str:
        if not isinstance(wardrobe_data, dict):
            return ""
        profile = wardrobe_data.get("style_profile")
        if not isinstance(profile, dict):
            return ""

        profile_lines = []
        profile_fields = [
            ("favorite_styles", "Favorite styles"),
            ("preferred_colors", "Preferred colors"),
            ("fit_preferences", "Fit preferences"),
        ]
        for key, label in profile_fields:
            value = clean_text(profile.get(key), "")
            if value:
                profile_lines.append(f"{label}: {value}")

        if not profile_lines:
            return ""
        return "Saved style profile:\n" + "\n".join(profile_lines)

    def pick_wardrobe_piece(items: list[dict]) -> dict | None:
        category = clean_text(new_item.get("category"), "").lower()
        category_preferences = {
            "tops": ["bottoms", "shoes", "outerwear", "accessories"],
            "bottoms": ["tops", "shoes", "outerwear", "accessories"],
            "outerwear": ["tops", "bottoms", "shoes", "accessories"],
            "shoes": ["bottoms", "tops", "outerwear", "accessories"],
            "accessories": ["tops", "bottoms", "shoes", "outerwear"],
        }
        for preferred_category in category_preferences.get(category, []):
            for item in items:
                item_category = clean_text(item.get("category"), "").lower()
                if item_category == preferred_category:
                    return item
        return items[0] if items else None

    def fallback_suggestion(items: list[dict]) -> str:
        thrift_item = item_name(new_item)
        item_styles = clean_text(new_item.get("style_tags"), "")
        aesthetic = item_styles if item_styles else "secondhand"
        wardrobe_piece = pick_wardrobe_piece(items)

        if wardrobe_piece:
            piece_name = item_name(wardrobe_piece)
            return (
                f"Style {thrift_item} with your {piece_name} for a cohesive "
                f"{aesthetic} outfit. Add a simple base layer or neutral shoe "
                "so the thrifted piece stays central. For a practical finish, "
                "balance the silhouette by tucking or cuffing one piece if the "
                "outfit starts to feel too loose."
            )

        colors = clean_text(new_item.get("colors"), "its main colors")
        return (
            f"Build a {aesthetic} outfit around {thrift_item} by pairing it "
            f"with simple basics that echo {colors}. Keep the rest of the look "
            "easy, like denim, a clean jacket, or everyday sneakers. For a "
            "practical styling tip, balance the proportions with a tuck, cuff, "
            "or fitted layer."
        )

    wardrobe_items = valid_wardrobe_items(wardrobe)
    selected_item_text = format_listing(new_item)
    style_profile_text = format_style_profile(wardrobe)
    if wardrobe_items:
        wardrobe_text = "\n".join(
            format_wardrobe_item(item) for item in wardrobe_items
        )
        user_prompt = f"""
Selected thrift item:
{selected_item_text}

Available wardrobe pieces:
{wardrobe_text}

{style_profile_text}

Suggest one complete outfit using the selected thrift item and compatible
wardrobe pieces. Mention the selected thrift item, at least one wardrobe
piece by name, the overall aesthetic, and one practical styling tip such as
layering, cuffing, tucking, color balance, or shoe choice. Keep it concise:
3 to 5 sentences.
"""
    else:
        user_prompt = f"""
Selected thrift item:
{selected_item_text}

{style_profile_text}

The user's wardrobe is empty or unavailable. Suggest useful general styling
advice for this item. Mention the selected thrift item, the overall aesthetic,
and one practical styling tip such as layering, cuffing, tucking, color
balance, or shoe choice. Keep it concise: 3 to 5 sentences.
"""

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are FitFindr, a concise secondhand-fashion "
                        "stylist. Return one practical outfit suggestion in "
                        "3 to 5 sentences."
                    ),
                },
                {"role": "user", "content": user_prompt.strip()},
            ],
            temperature=0.7,
            max_tokens=220,
        )
        suggestion = response.choices[0].message.content.strip()
        return suggestion or fallback_suggestion(wardrobe_items)
    except Exception:
        return fallback_suggestion(wardrobe_items)


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
    outfit_error = (
        "I need a complete outfit suggestion before I can create a fit card."
    )

    if not isinstance(outfit, str):
        return outfit_error

    outfit_text = outfit.strip()
    if (
        not outfit_text
        or outfit_text.lower() in {"none", "null", "n/a", "na"}
        or len(outfit_text.split()) < 5
    ):
        return outfit_error

    if not isinstance(new_item, dict) or not new_item:
        return (
            "I need a valid selected listing before I can create a fit card."
        )

    def clean_text(value, default: str = "") -> str:
        if value is None:
            return default
        if isinstance(value, list):
            cleaned_items = [
                str(item).strip() for item in value if str(item).strip()
            ]
            return ", ".join(cleaned_items) if cleaned_items else default
        text = str(value).strip()
        return text if text else default

    item_title = clean_text(new_item.get("title") or new_item.get("name"))
    item_context = [
        clean_text(new_item.get("category")),
        clean_text(new_item.get("description")),
        clean_text(new_item.get("style_tags")),
        clean_text(new_item.get("colors")),
        clean_text(new_item.get("brand")),
    ]
    if not item_title or not any(item_context):
        return (
            "I need a valid selected listing with item details before I can "
            "create a fit card."
        )

    def format_price(value) -> str:
        if value is None or value == "":
            return ""
        try:
            return f"${float(value):.2f}".rstrip("0").rstrip(".")
        except (TypeError, ValueError):
            return str(value).strip()

    def fallback_caption() -> str:
        price = format_price(new_item.get("price"))
        platform = clean_text(new_item.get("platform"))
        aesthetic = clean_text(new_item.get("style_tags"), "secondhand")
        source_parts = []
        if price:
            source_parts.append(price)
        if platform:
            source_parts.append(f"on {platform}")
        source_text = f" ({' '.join(source_parts)})" if source_parts else ""
        return (
            f"{item_title}{source_text} pulls the whole outfit into a "
            f"{aesthetic} vibe without feeling too styled. The fit feels "
            "casual and lived-in, with the thrifted piece doing the main work."
        )

    selected_item_text = "\n".join(
        [
            f"Title: {item_title}",
            f"Category: {clean_text(new_item.get('category'), 'unspecified')}",
            f"Brand: {clean_text(new_item.get('brand'), 'unspecified')}",
            f"Colors: {clean_text(new_item.get('colors'), 'unspecified')}",
            f"Style tags: {clean_text(new_item.get('style_tags'), 'unspecified')}",
            f"Price: {format_price(new_item.get('price')) or 'unspecified'}",
            f"Platform: {clean_text(new_item.get('platform'), 'unspecified')}",
            f"Description: {clean_text(new_item.get('description'), 'unspecified')}",
        ]
    )

    prompt = f"""
Selected thrift item:
{selected_item_text}

Outfit suggestion:
{outfit_text}

Create one short social-media-style outfit caption. Keep it to 1 to 3
sentences. Mention the thrifted item naturally, mention the price or platform
when available, and capture the vibe of the outfit. Do not write a product
description, bullet list, title, or hashtags.
"""

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are FitFindr, a casual secondhand-fashion "
                        "caption writer. Write concise, natural social "
                        "captions that sound like a real outfit post."
                    ),
                },
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=0.9,
            max_tokens=140,
        )
        caption = response.choices[0].message.content.strip()
        return caption or fallback_caption()
    except Exception:
        return fallback_caption()


# ── Stretch Tool: compare_price ───────────────────────────────────────────────

def compare_price(new_item: dict, search_results: list[dict]) -> str:
    """
    Compare the selected listing price with similar listings from the current
    search results and return a short low/fair/high assessment.
    """
    limited_message = (
        "Price comparison is limited because there are not enough comparable "
        "listings with valid prices."
    )

    def normalize(value) -> str:
        return str(value or "").lower().strip()

    def tokenize(value) -> set[str]:
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
        return {
            token
            for token in re.findall(r"[a-z0-9]+", normalize(value))
            if token not in stop_words
        }

    def value_set(value) -> set[str]:
        if isinstance(value, list):
            return {
                normalize(item)
                for item in value
                if normalize(item)
            }
        normalized = normalize(value)
        return {normalized} if normalized else set()

    def get_price(item: dict) -> float | None:
        try:
            price = float(item.get("price"))
        except (TypeError, ValueError, AttributeError):
            return None
        return price if price >= 0 else None

    def format_price(price: float) -> str:
        return f"${price:.2f}".rstrip("0").rstrip(".")

    if not isinstance(new_item, dict) or not new_item:
        return "Price comparison is limited because the selected item is invalid."

    selected_price = get_price(new_item)
    if selected_price is None:
        return (
            "Price comparison is limited because the selected item is missing "
            "a valid price."
        )

    if not isinstance(search_results, list):
        return limited_message

    selected_id = normalize(new_item.get("id"))
    selected_category = normalize(new_item.get("category"))
    selected_styles = value_set(new_item.get("style_tags"))
    selected_colors = value_set(new_item.get("colors"))
    selected_title_words = tokenize(new_item.get("title"))

    comparable_prices = []
    for listing in search_results:
        if not isinstance(listing, dict) or not listing:
            continue
        if listing is new_item:
            continue
        if selected_id and normalize(listing.get("id")) == selected_id:
            continue

        listing_price = get_price(listing)
        if listing_price is None:
            continue

        listing_category = normalize(listing.get("category"))
        listing_styles = value_set(listing.get("style_tags"))
        listing_colors = value_set(listing.get("colors"))
        listing_title_words = tokenize(listing.get("title"))

        has_category_match = (
            bool(selected_category)
            and selected_category == listing_category
        )
        has_style_match = bool(selected_styles & listing_styles)
        has_color_match = bool(selected_colors & listing_colors)
        has_title_match = bool(selected_title_words & listing_title_words)

        if any(
            [
                has_category_match,
                has_style_match,
                has_color_match,
                has_title_match,
            ]
        ):
            comparable_prices.append(listing_price)

    if len(comparable_prices) < 2:
        return limited_message

    comparable_prices.sort()
    middle = len(comparable_prices) // 2
    if len(comparable_prices) % 2 == 0:
        typical_price = (
            comparable_prices[middle - 1] + comparable_prices[middle]
        ) / 2
    else:
        typical_price = comparable_prices[middle]

    if selected_price <= typical_price * 0.85:
        assessment = "low"
    elif selected_price >= typical_price * 1.15:
        assessment = "high"
    else:
        assessment = "fair"

    price_range = (
        f"{format_price(comparable_prices[0])}-"
        f"{format_price(comparable_prices[-1])}"
    )
    item_name = (
        new_item.get("title")
        or new_item.get("name")
        or "This item"
    )
    return (
        f"{item_name} at {format_price(selected_price)} looks {assessment} "
        f"compared with similar listings in the {price_range} range."
    )

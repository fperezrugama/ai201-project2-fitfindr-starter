import sys
import types
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import groq  # noqa: F401
except ModuleNotFoundError:
    groq_stub = types.ModuleType("groq")
    groq_stub.Groq = lambda *args, **kwargs: None
    sys.modules["groq"] = groq_stub

try:
    import dotenv  # noqa: F401
except ModuleNotFoundError:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub

import pytest

import tools
from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


class FakeGroqClient:
    class Chat:
        class Completions:
            def create(self, **kwargs):
                content = (
                    "Style the thrifted graphic tee with baggy jeans for a "
                    "vintage streetwear look. Add sneakers and a small tuck "
                    "to keep the proportions balanced."
                )
                message = types.SimpleNamespace(content=content)
                choice = types.SimpleNamespace(message=message)
                return types.SimpleNamespace(choices=[choice])

        completions = Completions()

    chat = Chat()


@pytest.fixture(autouse=True)
def fake_groq_client(monkeypatch):
    monkeypatch.setattr(tools, "_get_groq_client", lambda: FakeGroqClient())


@pytest.fixture
def sample_item():
    return search_listings("vintage graphic tee", size=None, max_price=50)[0]


def test_search_listings_returns_non_empty_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert results
    assert isinstance(results, list)


def test_search_listings_top_result_is_direct_tee_match():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    top_result = results[0]
    searchable_text = " ".join(
        [
            top_result.get("title", ""),
            " ".join(top_result.get("style_tags", [])),
        ]
    ).lower()

    assert "graphic tee" in searchable_text or "band tee" in searchable_text


def test_search_listings_no_match_returns_empty_list():
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_listings_respects_max_price_if_results_exist():
    results = search_listings("jacket", size=None, max_price=10)

    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_with_example_wardrobe_returns_string(sample_item):
    result = suggest_outfit(sample_item, get_example_wardrobe())

    assert isinstance(result, str)
    assert result.strip()


def test_suggest_outfit_with_empty_wardrobe_returns_string(sample_item):
    result = suggest_outfit(sample_item, get_empty_wardrobe())

    assert isinstance(result, str)
    assert result.strip()


def test_suggest_outfit_invalid_item_returns_helpful_error():
    result = suggest_outfit({}, get_example_wardrobe())

    assert isinstance(result, str)
    assert "missing or invalid" in result.lower()


def test_create_fit_card_empty_outfit_returns_helpful_error(sample_item):
    result = create_fit_card("", sample_item)

    assert isinstance(result, str)
    assert "complete outfit suggestion" in result.lower()


def test_create_fit_card_valid_outfit_returns_caption(sample_item):
    valid_outfit = (
        "Wear the thrifted graphic tee with baggy jeans and sneakers for a "
        "vintage streetwear look. Tuck the front slightly for balance."
    )
    result = create_fit_card(valid_outfit, sample_item)

    assert isinstance(result, str)
    assert result.strip()

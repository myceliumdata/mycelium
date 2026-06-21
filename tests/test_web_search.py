"""Smoke tests for pluggable web search (mocked; no live API)."""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

import pytest

from tools.web_search import (
    SearchHit,
    UnknownSearchProviderError,
    WebSearchNotConfiguredError,
    WebSearchProviderError,
    _normalize_brave_hits,
    _normalize_exa_hits,
    _normalize_tavily_hits,
    create_web_search_tool,
    is_web_search_available,
    search_provider,
    web_search,
)


@pytest.mark.smoke
def test_search_provider_defaults_to_tavily(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    assert search_provider() == "tavily"


@pytest.mark.smoke
def test_search_provider_rejects_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEARCH_PROVIDER", "serper")
    with pytest.raises(UnknownSearchProviderError):
        search_provider()


@pytest.mark.smoke
def test_normalize_hits_from_tavily_shape() -> None:
    raw = {
        "query": "test",
        "results": [
            {
                "url": "https://example.com/a",
                "title": "Example A",
                "content": "Snippet A",
                "score": 0.9,
            },
            {"url": "", "title": "skip"},
        ],
    }
    hits = _normalize_tavily_hits(raw)
    assert len(hits) == 1
    assert hits[0] == SearchHit(
        title="Example A",
        url="https://example.com/a",
        snippet="Snippet A",
        score=0.9,
    )


@pytest.mark.smoke
def test_normalize_hits_from_exa_shape() -> None:
    raw = {
        "results": [
            {
                "url": "https://example.com/exa",
                "title": "Exa Hit",
                "text": "Body text",
                "score": 0.42,
            },
            {
                "url": "https://example.com/highlights",
                "title": "Highlights Hit",
                "highlights": ["one", "two"],
            },
        ],
    }
    hits = _normalize_exa_hits(raw)
    assert len(hits) == 2
    assert hits[0].url == "https://example.com/exa"
    assert hits[0].snippet == "Body text"
    assert hits[1].snippet == "one two"


@pytest.mark.smoke
def test_normalize_hits_from_exa_object_results() -> None:
    raw = SimpleNamespace(
        results=[
            SimpleNamespace(
                url="https://example.com/obj",
                title="Object Hit",
                text="From object",
                score=0.7,
            ),
        ],
    )
    hits = _normalize_exa_hits(raw)
    assert len(hits) == 1
    assert hits[0].url == "https://example.com/obj"
    assert hits[0].snippet == "From object"


@pytest.mark.smoke
def test_normalize_hits_from_brave_json_string() -> None:
    raw = json.dumps(
        [
            {
                "title": "Brave JSON",
                "link": "https://example.com/brave-json",
                "snippet": "From JSON string",
            },
        ],
    )
    hits = _normalize_brave_hits(raw)
    assert len(hits) == 1
    assert hits[0].url == "https://example.com/brave-json"


@pytest.mark.smoke
def test_normalize_hits_from_brave_shape() -> None:
    raw = [
        {
            "title": "Brave Hit",
            "link": "https://example.com/brave",
            "snippet": "Brave snippet",
        },
    ]
    hits = _normalize_brave_hits(raw)
    assert len(hits) == 1
    assert hits[0] == SearchHit(
        title="Brave Hit",
        url="https://example.com/brave",
        snippet="Brave snippet",
    )


@pytest.mark.smoke
def test_is_web_search_available_respects_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEARCH_PROVIDER", "exa")
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    assert not is_web_search_available()

    monkeypatch.setenv("EXA_API_KEY", "exa-test")
    assert is_web_search_available()


@pytest.mark.smoke
def test_web_search_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert not is_web_search_available()
    with pytest.raises(WebSearchNotConfiguredError):
        web_search("anything")


@pytest.mark.smoke
def test_web_search_invokes_provider_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")

    class FakeTool:
        def invoke(self, args: dict) -> dict:
            assert args["query"] == "Paul Murphy employer"
            return {
                "results": [
                    {
                        "url": "https://example.com/paul",
                        "title": "Paul Murphy",
                        "content": "Works at Example Co",
                        "score": 0.8,
                    },
                ],
            }

    import importlib

    web_search_mod = importlib.import_module("tools.web_search")
    monkeypatch.setattr(
        web_search_mod,
        "_search_tavily",
        lambda query, **_: FakeTool().invoke({"query": query}),
    )

    hits = web_search("Paul Murphy employer", max_results=3)
    assert len(hits) == 1
    assert hits[0].url == "https://example.com/paul"
    assert "Example Co" in hits[0].snippet


@pytest.mark.smoke
def test_create_web_search_tool_uses_web_search_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
    tool = create_web_search_tool()
    assert tool.name == "web_search"


@pytest.mark.smoke
def test_web_search_empty_query_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
    assert web_search("   ") == []


@pytest.mark.smoke
def test_tavily_error_dict_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
    web_search_mod = importlib.import_module("tools.web_search")
    monkeypatch.setattr(
        web_search_mod,
        "_search_tavily",
        lambda query, **_: {"error": ValueError("Error 432: usage limit exceeded")},
    )
    with pytest.raises(WebSearchProviderError, match="432"):
        web_search("test query")


@pytest.mark.smoke
def test_exa_error_string_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEARCH_PROVIDER", "exa")
    monkeypatch.setenv("EXA_API_KEY", "exa-test-key")
    web_search_mod = importlib.import_module("tools.web_search")
    monkeypatch.setattr(
        web_search_mod,
        "_search_exa",
        lambda query, **_: "HTTPError('403 Client Error: Forbidden')",
    )
    with pytest.raises(WebSearchProviderError):
        web_search("test query")


@pytest.mark.smoke
def test_web_search_exa_backend_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEARCH_PROVIDER", "exa")
    monkeypatch.setenv("EXA_API_KEY", "exa-test-key")
    web_search_mod = importlib.import_module("tools.web_search")
    monkeypatch.setattr(
        web_search_mod,
        "_search_exa",
        lambda query, **_: {
            "results": [
                {
                    "url": "https://example.com/exa-live",
                    "title": "Exa",
                    "text": "Exa body",
                },
            ],
        },
    )
    hits = web_search("exa query")
    assert len(hits) == 1
    assert hits[0].url == "https://example.com/exa-live"


@pytest.mark.smoke
def test_web_search_brave_backend_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEARCH_PROVIDER", "brave")
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "brave-test-key")
    web_search_mod = importlib.import_module("tools.web_search")
    monkeypatch.setattr(
        web_search_mod,
        "_search_brave",
        lambda query, **_: [
            {
                "title": "Brave",
                "link": "https://example.com/brave-live",
                "snippet": "Brave body",
            },
        ],
    )
    hits = web_search("brave query")
    assert len(hits) == 1
    assert hits[0].url == "https://example.com/brave-live"
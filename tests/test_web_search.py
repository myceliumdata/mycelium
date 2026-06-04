"""Smoke tests for Tavily web search wrapper (mocked; no live API)."""

from __future__ import annotations

import pytest

from tools.tavily import (
    SearchHit,
    WebSearchNotConfiguredError,
    _normalize_hits,
    is_web_search_available,
    web_search,
)


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
    hits = _normalize_hits(raw)
    assert len(hits) == 1
    assert hits[0] == SearchHit(
        title="Example A",
        url="https://example.com/a",
        snippet="Snippet A",
        score=0.9,
    )


@pytest.mark.smoke
def test_web_search_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert not is_web_search_available()
    with pytest.raises(WebSearchNotConfiguredError):
        web_search("anything")


@pytest.mark.smoke
def test_web_search_invokes_tavily_tool(monkeypatch: pytest.MonkeyPatch) -> None:
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

    import tools.tavily as tavily_mod

    monkeypatch.setattr(tavily_mod, "create_tavily_search_tool", lambda **_: FakeTool())

    hits = web_search("Paul Murphy employer", max_results=3)
    assert len(hits) == 1
    assert hits[0].url == "https://example.com/paul"
    assert "Example Co" in hits[0].snippet


@pytest.mark.smoke
def test_web_search_empty_query_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
    assert web_search("   ") == []
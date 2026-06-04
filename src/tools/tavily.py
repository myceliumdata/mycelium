"""Web search for specialist research (Tavily-backed).

Specialists and future research runners should call :func:`web_search` or bind
:func:`create_tavily_search_tool` for LangChain agents. Requires ``TAVILY_API_KEY``.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field


class WebSearchNotConfiguredError(RuntimeError):
    """Raised when ``TAVILY_API_KEY`` is missing."""


class SearchHit(BaseModel):
    """Normalized search result for prompts and storage."""

    title: str = ""
    url: str = ""
    snippet: str = Field(
        default="",
        description="Short excerpt (Tavily ``content`` field).",
    )
    score: float | None = None


def is_web_search_available() -> bool:
    """True when Tavily credentials are present in the environment."""
    return bool(os.getenv("TAVILY_API_KEY", "").strip())


def _require_api_key() -> str:
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        msg = (
            "TAVILY_API_KEY is not set. Add it to .env (see .env.example) "
            "or export it before calling web search."
        )
        raise WebSearchNotConfiguredError(msg)
    return key


def _normalize_hits(raw: Any) -> list[SearchHit]:
    """Map Tavily / LangChain tool output to :class:`SearchHit` list."""
    if not isinstance(raw, dict):
        return []
    rows = raw.get("results")
    if not isinstance(rows, list):
        return []
    hits: list[SearchHit] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or "")
        if not url:
            continue
        hits.append(
            SearchHit(
                title=str(row.get("title") or ""),
                url=url,
                snippet=str(row.get("content") or row.get("snippet") or ""),
                score=float(row["score"]) if row.get("score") is not None else None,
            ),
        )
    return hits


def create_tavily_search_tool(
    *,
    max_results: int = 5,
    topic: str = "general",
    search_depth: str = "basic",
):
    """
    LangChain ``TavilySearch`` tool for agent tool-calling loops.

    Caller must ensure ``TAVILY_API_KEY`` is set (see :func:`is_web_search_available`).
    """
    _require_api_key()
    from langchain_tavily import TavilySearch

    return TavilySearch(
        max_results=max_results,
        topic=topic,
        search_depth=search_depth,
    )


def web_search(
    query: str,
    *,
    max_results: int = 5,
    topic: str = "general",
    search_depth: str = "basic",
) -> list[SearchHit]:
    """
    Run a Tavily web search and return normalized hits.

    Args:
        query: Natural-language search query.
        max_results: Maximum results (Tavily default is 5).
        topic: Tavily topic filter: ``general``, ``news``, or ``finance``.
        search_depth: ``basic`` or ``advanced``.

    Raises:
        WebSearchNotConfiguredError: if ``TAVILY_API_KEY`` is unset.
    """
    q = query.strip()
    if not q:
        return []

    tool = create_tavily_search_tool(
        max_results=max_results,
        topic=topic,
        search_depth=search_depth,
    )
    raw = tool.invoke({"query": q})
    return _normalize_hits(raw)
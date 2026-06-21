"""Pluggable web search for specialist research (Tavily, Exa, or Brave).

Specialists and research runners should call :func:`web_search` or bind
:func:`create_web_search_tool` for LangChain agents. Select the backend with
``SEARCH_PROVIDER`` (``tavily``, ``exa``, or ``brave``).
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

SearchProvider = Literal["tavily", "exa", "brave"]

_SEARCH_PROVIDERS: tuple[SearchProvider, ...] = ("tavily", "exa", "brave")

_PROVIDER_KEY_ENV: dict[SearchProvider, str] = {
    "tavily": "TAVILY_API_KEY",
    "exa": "EXA_API_KEY",
    "brave": "BRAVE_SEARCH_API_KEY",
}


class WebSearchNotConfiguredError(RuntimeError):
    """Raised when the active search provider's API key is missing."""


class WebSearchProviderError(RuntimeError):
    """Raised when the search provider returns an error payload instead of results."""


class UnknownSearchProviderError(ValueError):
    """Raised when ``SEARCH_PROVIDER`` is not a supported value."""


class SearchHit(BaseModel):
    """Normalized search result for prompts and storage."""

    title: str = ""
    url: str = ""
    snippet: str = Field(
        default="",
        description="Short excerpt from the provider result body.",
    )
    score: float | None = None


def search_provider() -> SearchProvider:
    """Active search backend from ``SEARCH_PROVIDER`` (default: ``tavily``)."""
    raw = os.getenv("SEARCH_PROVIDER", "tavily").strip().lower()
    if raw not in _SEARCH_PROVIDERS:
        supported = ", ".join(_SEARCH_PROVIDERS)
        msg = f"SEARCH_PROVIDER must be one of {supported}; got {raw!r}"
        raise UnknownSearchProviderError(msg)
    return raw  # type: ignore[return-value]


def active_search_api_key_env() -> str:
    """Env var name for the active provider's API key (for gate skip / diagnostics)."""
    return _PROVIDER_KEY_ENV[search_provider()]


def is_web_search_available() -> bool:
    """True when credentials for the active ``SEARCH_PROVIDER`` are present."""
    try:
        provider = search_provider()
    except UnknownSearchProviderError:
        return False
    env_name = _PROVIDER_KEY_ENV[provider]
    return bool(os.getenv(env_name, "").strip())


def _require_api_key(provider: SearchProvider | None = None) -> str:
    active = provider or search_provider()
    env_name = _PROVIDER_KEY_ENV[active]
    key = os.getenv(env_name, "").strip()
    if not key:
        msg = (
            f"{env_name} is not set for SEARCH_PROVIDER={active!r}. "
            "Add it to .env (see .env.example) or export it before calling web search."
        )
        raise WebSearchNotConfiguredError(msg)
    return key


def _normalize_tavily_hits(raw: Any) -> list[SearchHit]:
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


def _normalize_exa_hits(raw: Any) -> list[SearchHit]:
    rows: list[Any]
    if hasattr(raw, "results"):
        rows = list(getattr(raw, "results") or [])
    elif isinstance(raw, dict) and isinstance(raw.get("results"), list):
        rows = raw["results"]
    elif isinstance(raw, list):
        rows = raw
    else:
        return []

    hits: list[SearchHit] = []
    for row in rows:
        url = ""
        title = ""
        snippet = ""
        score: float | None = None
        if isinstance(row, dict):
            url = str(row.get("url") or "")
            title = str(row.get("title") or "")
            snippet = str(row.get("text") or row.get("snippet") or "")
            highlights = row.get("highlights")
            if not snippet and isinstance(highlights, list):
                snippet = " ".join(str(h) for h in highlights)
            if row.get("score") is not None:
                score = float(row["score"])
        else:
            url = str(getattr(row, "url", "") or "")
            title = str(getattr(row, "title", "") or "")
            text = getattr(row, "text", None)
            highlights = getattr(row, "highlights", None)
            if text:
                snippet = str(text)
            elif highlights:
                snippet = " ".join(str(h) for h in highlights)
            raw_score = getattr(row, "score", None)
            if raw_score is not None:
                score = float(raw_score)
        if not url:
            continue
        hits.append(
            SearchHit(title=title, url=url, snippet=snippet, score=score),
        )
    return hits


def _normalize_brave_hits(raw: Any) -> list[SearchHit]:
    rows: list[Any]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        rows = parsed if isinstance(parsed, list) else []
    elif isinstance(raw, list):
        rows = raw
    else:
        return []

    hits: list[SearchHit] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("link") or row.get("url") or "")
        if not url:
            continue
        hits.append(
            SearchHit(
                title=str(row.get("title") or ""),
                url=url,
                snippet=str(row.get("snippet") or row.get("description") or ""),
            ),
        )
    return hits


def _validate_provider_raw(raw: Any, *, provider: SearchProvider) -> None:
    """Fail loud when a provider returns an error payload instead of results."""
    if isinstance(raw, BaseException):
        raise WebSearchProviderError(str(raw)) from raw

    if provider == "tavily" and isinstance(raw, dict):
        err = raw.get("error")
        if err is not None:
            raise WebSearchProviderError(str(err))
        return

    if not isinstance(raw, str):
        return
    text = raw.strip()
    if not text:
        return
    if text.startswith(("HTTP", "Error", "Exception", "ApiError", "ClientError")):
        raise WebSearchProviderError(text)
    if "Error" in text and "results" not in text.lower():
        raise WebSearchProviderError(text)


def _normalize_hits(raw: Any, *, provider: SearchProvider) -> list[SearchHit]:
    if provider == "tavily":
        return _normalize_tavily_hits(raw)
    if provider == "exa":
        return _normalize_exa_hits(raw)
    return _normalize_brave_hits(raw)


def _hits_to_tool_payload(query: str, hits: list[SearchHit]) -> dict[str, Any]:
    return {
        "query": query.strip(),
        "results": [
            {
                "url": hit.url,
                "title": hit.title,
                "content": hit.snippet,
                **({"score": hit.score} if hit.score is not None else {}),
            }
            for hit in hits
        ],
    }


def _search_tavily(
    query: str,
    *,
    max_results: int,
    topic: str,
    search_depth: str,
) -> Any:
    from langchain_tavily import TavilySearch

    tool = TavilySearch(
        max_results=max_results,
        topic=topic,
        search_depth=search_depth,
        tavily_api_key=_require_api_key("tavily"),
    )
    return tool.invoke({"query": query})


def _search_exa(query: str, *, max_results: int) -> Any:
    from langchain_exa import ExaSearchResults

    tool = ExaSearchResults(
        exa_api_key=_require_api_key("exa"),
    )
    return tool.invoke(
        {
            "query": query,
            "num_results": max_results,
            "text_contents_options": {"max_characters": 2000},
            "type": "auto",
        },
    )


def _search_brave(query: str, *, max_results: int) -> Any:
    from langchain_community.tools import BraveSearch

    tool = BraveSearch.from_api_key(
        _require_api_key("brave"),
        search_kwargs={"count": max_results},
    )
    return tool.invoke(query)


def _run_provider_search(
    query: str,
    *,
    provider: SearchProvider,
    max_results: int,
    topic: str,
    search_depth: str,
) -> Any:
    if provider == "tavily":
        return _search_tavily(
            query,
            max_results=max_results,
            topic=topic,
            search_depth=search_depth,
        )
    if provider == "exa":
        return _search_exa(query, max_results=max_results)
    return _search_brave(query, max_results=max_results)


class _WebSearchLangChainTool(BaseTool):
    """LangChain tool named ``web_search`` (matches research prompt templates)."""

    name: str = "web_search"
    description: str = (
        "Search the public web for fresh facts. "
        "Input should be a focused search query string."
    )

    max_results: int = 5
    topic: str = "general"
    search_depth: str = "basic"

    def _run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        hits = web_search(
            query,
            max_results=self.max_results,
            topic=self.topic,
            search_depth=self.search_depth,
        )
        return _hits_to_tool_payload(query, hits)


def create_web_search_tool(
    *,
    max_results: int = 5,
    topic: str = "general",
    search_depth: str = "basic",
) -> _WebSearchLangChainTool:
    """
    LangChain tool for agent tool-calling loops.

    Always exposes tool name ``web_search``. ``topic`` and ``search_depth`` apply
    only when ``SEARCH_PROVIDER=tavily``.
    """
    _require_api_key()
    return _WebSearchLangChainTool(
        max_results=max_results,
        topic=topic,
        search_depth=search_depth,
    )


def create_tavily_search_tool(
    *,
    max_results: int = 5,
    topic: str = "general",
    search_depth: str = "basic",
) -> Any:
    """
    LangChain ``TavilySearch`` tool (Tavily provider only).

    Prefer :func:`create_web_search_tool` for provider-agnostic research.
    """
    _require_api_key("tavily")
    from langchain_tavily import TavilySearch

    return TavilySearch(
        max_results=max_results,
        topic=topic,
        search_depth=search_depth,
        tavily_api_key=_require_api_key("tavily"),
    )


def web_search(
    query: str,
    *,
    max_results: int = 5,
    topic: str = "general",
    search_depth: str = "basic",
    provider: SearchProvider | None = None,
) -> list[SearchHit]:
    """
    Run a web search via the active provider and return normalized hits.

    Args:
        query: Natural-language search query.
        max_results: Maximum results to return.
        topic: Tavily topic filter (``general``, ``news``, ``finance``).
        search_depth: Tavily depth (``basic``, ``advanced``, etc.).
        provider: Override ``SEARCH_PROVIDER`` for this call only.

    Raises:
        WebSearchNotConfiguredError: if the active provider's API key is unset.
        WebSearchProviderError: if the provider returns an error payload.
        UnknownSearchProviderError: if ``SEARCH_PROVIDER`` is invalid.
    """
    q = query.strip()
    if not q:
        return []

    active = provider or search_provider()
    _require_api_key(active)
    raw = _run_provider_search(
        q,
        provider=active,
        max_results=max_results,
        topic=topic,
        search_depth=search_depth,
    )
    _validate_provider_raw(raw, provider=active)
    return _normalize_hits(raw, provider=active)
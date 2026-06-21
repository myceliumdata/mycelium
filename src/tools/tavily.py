"""Backward-compatible re-exports for Tavily-era imports.

Prefer :mod:`tools.web_search` for provider-agnostic search.
"""

from tools.web_search import (
    SearchHit,
    SearchProvider,
    UnknownSearchProviderError,
    WebSearchNotConfiguredError,
    WebSearchProviderError,
    active_search_api_key_env,
    create_tavily_search_tool,
    create_web_search_tool,
    is_web_search_available,
    search_provider,
    web_search,
)

__all__ = [
    "SearchHit",
    "SearchProvider",
    "UnknownSearchProviderError",
    "WebSearchNotConfiguredError",
    "WebSearchProviderError",
    "active_search_api_key_env",
    "create_tavily_search_tool",
    "create_web_search_tool",
    "is_web_search_available",
    "search_provider",
    "web_search",
]
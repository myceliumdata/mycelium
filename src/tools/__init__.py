"""Shared tools for specialist research and future agent capabilities."""

from tools.tavily import (
    SearchHit,
    WebSearchNotConfiguredError,
    create_tavily_search_tool,
    is_web_search_available,
    web_search,
)

__all__ = [
    "SearchHit",
    "WebSearchNotConfiguredError",
    "create_tavily_search_tool",
    "is_web_search_available",
    "web_search",
]
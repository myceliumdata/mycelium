"""Shared tools for specialist research and future agent capabilities."""

from tools.research import (
    FieldProposal,
    ResearchProposal,
    ResearchRunResult,
    build_research_prompts,
    is_research_available,
    load_category_metadata,
    run_field_research,
)
from tools.web_search import (
    SearchHit,
    SearchProvider,
    UnknownSearchProviderError,
    WebSearchNotConfiguredError,
    create_tavily_search_tool,
    create_web_search_tool,
    is_web_search_available,
    search_provider,
    web_search,
)

__all__ = [
    "FieldProposal",
    "ResearchProposal",
    "ResearchRunResult",
    "SearchHit",
    "SearchProvider",
    "UnknownSearchProviderError",
    "WebSearchNotConfiguredError",
    "build_research_prompts",
    "create_tavily_search_tool",
    "create_web_search_tool",
    "is_research_available",
    "is_web_search_available",
    "load_category_metadata",
    "run_field_research",
    "search_provider",
    "web_search",
]
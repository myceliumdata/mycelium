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
from tools.tavily import (
    SearchHit,
    WebSearchNotConfiguredError,
    create_tavily_search_tool,
    is_web_search_available,
    web_search,
)

__all__ = [
    "FieldProposal",
    "ResearchProposal",
    "ResearchRunResult",
    "SearchHit",
    "WebSearchNotConfiguredError",
    "build_research_prompts",
    "create_tavily_search_tool",
    "is_research_available",
    "is_web_search_available",
    "load_category_metadata",
    "run_field_research",
    "web_search",
]
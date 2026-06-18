"""Pydantic models for the Phase 1 classification engine (see docs/plans/classification-engine-phase1.md)."""

from datetime import datetime

from pydantic import BaseModel, Field


class Category(BaseModel):
    """A data category/domain that can be assigned to attributes.

    The category *name* is the dict key in CategoryTreeData.categories (no duplication
    inside the value object). This keeps the persisted JSON clean and the lookup index simple.
    """

    description: str
    assigned_agent: str  # e.g. "contact_specialist", "core_data" (Phase 1 uses core_data for unknowns too), or future specialist name
    examples: list[str] = Field(default_factory=list)


class CategoryTreeData(BaseModel):
    """The serializable shape of the entire tree (written to JSON)."""

    version: str = "1.0"
    last_updated: datetime
    model_used: str = ""  # e.g. "gpt-4o-mini" (set on last LLM refresh)
    ontology_pack: str | None = None  # committed example-pack id when set
    categories: dict[str, Category]  # category_name -> Category (name is the key)
    attribute_map: dict[str, str]  # normalized_attribute (lower) -> category_name (the fast lookup index)


class ClassificationResult(BaseModel):
    """What classify() returns (easy to JSON-serialize into audit/debug/state)."""

    attribute: str
    category: str
    assigned_agent: str | None
    description: str
    confidence: float


class CategoryProposal(BaseModel):
    """Structured output shape for the LLM refresh path only (never on hot path)."""

    attribute: str
    category: str
    description: str | None = None
    assigned_agent: str | None = None
    confidence: float = 0.0


class CategoryProposals(BaseModel):
    """Wrapper model so that with_structured_output(list[CategoryProposal]) works reliably
    with LangChain's OpenAI structured output conversion (avoids TypeError on list[...] schema).
    """

    proposals: list[CategoryProposal]

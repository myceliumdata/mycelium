"""Pydantic models for graph state, people queries, and JSON responses."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

# Strictly minimal core person fields (see docs/architecture.md)
CORE_PERSON_FIELDS: frozenset[str] = frozenset({"id", "name", "employer"})

MINIMUM_VIABLE_FIELDS: list[str] = ["name", "employer"]


class Person(BaseModel):
    """Core CRM person record — id, name, employer only."""

    id: str
    name: str
    employer: str | None = None

    def core_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class PersonQuery(BaseModel):
    """Inbound JSON query about a person."""

    person_key: str = Field(
        description="Person id or name used for core lookup (Phase 1)",
    )
    requested_attributes: list[str] = Field(
        default_factory=list,
        description="Non-core attributes requested; routed to specialist agents later",
    )
    provided_data: Person | None = Field(
        default=None,
        description="Minimum viable core data supplied to ingest a missing person",
    )


class PersonResponse(BaseModel):
    """Lightweight response for external consumers (CLI + MCP agents)."""

    results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Core person records as plain dicts (id, name, employer only). Always a list.",
    )
    message: str = Field(
        default="",
        description=(
            "Human- and agent-readable narrative. Primary channel for state, progress, and reasoning."
        ),
    )
    debug: str = Field(
        default="",
        description="Internal diagnostic information only. Not intended for external consumption.",
    )
    trace_id: str | None = Field(
        default=None,
        description=(
            "LangSmith trace id for this graph run, when tracing is enabled. "
            "Used to correlate responses with observability tooling."
        ),
    )
    thread_id: str | None = Field(
        default=None,
        description=(
            "LangGraph conversation thread id for this request. "
            "Used to correlate follow-up calls in the same session."
        ),
    )


class MyceliumGraphState(BaseModel):
    """LangGraph state for supervisor + specialist agents."""

    query: PersonQuery
    route: Literal["enrich"] | None = None
    response: PersonResponse | None = None
    person: Person | None = None
    validation_passed: bool | None = None
    validation_errors: Annotated[list[str], operator.add] = Field(default_factory=list)
    audit_log: Annotated[list[str], operator.add] = Field(default_factory=list)
    invocation_thread_id: str | None = Field(
        default=None,
        description="Conversation thread id propagated into PersonResponse (set by run_query).",
    )
    invocation_trace_id: str | None = Field(
        default=None,
        description="LangSmith trace id propagated into PersonResponse (set by run_query).",
    )


def non_core_attributes(requested: list[str]) -> list[str]:
    """Return requested attribute names that are outside the minimal core model."""
    normalized = [a.strip().lower() for a in requested if a.strip()]
    core_lower = {f.lower() for f in CORE_PERSON_FIELDS}
    return [attr for attr in normalized if attr not in core_lower]

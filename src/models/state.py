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


class DataRequest(BaseModel):
    """Structured request when a person is missing from core storage."""

    person_key: str
    required_fields: list[str] = Field(default_factory=lambda: list(MINIMUM_VIABLE_FIELDS))
    optional_fields: list[str] = Field(default_factory=list)
    message: str = "Person not found. Supply minimum viable fields to ingest."


class PersonResponse(BaseModel):
    """Outbound JSON response for MCP and CLI consumers."""

    status: Literal[
        "found",
        "data_request",
        "specialist_required",
        "ingested",
        "validation_failed",
    ]
    person: Person | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    data_request: DataRequest | None = None
    deferred_attributes: list[str] = Field(
        default_factory=list,
        description="Non-core attributes not served by core storage; specialist routing TBD",
    )
    message: str = ""
    errors: list[str] = Field(default_factory=list)


class MyceliumGraphState(BaseModel):
    """LangGraph state for supervisor + specialist agents."""

    query: PersonQuery
    route: Literal["enrich", "validator", "finish"] | None = None
    response: PersonResponse | None = None
    person: Person | None = None
    validation_passed: bool | None = None
    validation_errors: Annotated[list[str], operator.add] = Field(default_factory=list)
    audit_log: Annotated[list[str], operator.add] = Field(default_factory=list)


def non_core_attributes(requested: list[str]) -> list[str]:
    """Return requested attribute names that are outside the minimal core model."""
    normalized = [a.strip().lower() for a in requested if a.strip()]
    core_lower = {f.lower() for f in CORE_PERSON_FIELDS}
    return [attr for attr in normalized if attr not in core_lower]

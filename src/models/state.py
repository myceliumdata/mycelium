"""Pydantic models for graph state, people queries, and JSON responses."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

# Core CRM fields available without a derivative dataset
CORE_PERSON_FIELDS: frozenset[str] = frozenset(
    {"id", "name", "email", "employer", "phone", "title", "extra"},
)

# Attributes that always require a derivative dataset in Phase 1
DERIVATIVE_ONLY_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "age",
        "x_handle",
        "twitter_handle",
        "demographics",
        "linkedin_url",
        "location",
    },
)

MINIMUM_VIABLE_FIELDS: list[str] = ["name", "email", "employer"]


class Person(BaseModel):
    """Core CRM person record."""

    id: str
    name: str
    email: str | None = None
    employer: str | None = None
    phone: str | None = None
    title: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def core_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude={"extra"}, exclude_none=True)


class PersonQuery(BaseModel):
    """Inbound JSON query about a person."""

    person_key: str = Field(
        description="Person id, email, or exact name used for lookup",
    )
    requested_attributes: list[str] = Field(
        default_factory=list,
        description="Optional attributes beyond core CRM fields",
    )
    provided_data: Person | None = Field(
        default=None,
        description="Minimum viable data supplied to ingest a missing person",
    )


class DataRequest(BaseModel):
    """Structured request when a person is missing from core storage."""

    person_key: str
    required_fields: list[str] = Field(default_factory=lambda: list(MINIMUM_VIABLE_FIELDS))
    optional_fields: list[str] = Field(
        default_factory=lambda: ["phone", "title"],
    )
    message: str = "Person not found. Supply minimum viable fields to ingest."


class DerivativeDatasetRef(BaseModel):
    """Reference to a derivative dataset managed by a specialist agent (stub)."""

    dataset_id: str
    name: str
    attributes: list[str]
    status: Literal["pending", "stub_active"] = "pending"
    agent_stub: str = "derivative-agent-stub"


class PersonResponse(BaseModel):
    """Outbound JSON response for MCP and CLI consumers."""

    status: Literal[
        "found",
        "data_request",
        "derivative_pending",
        "ingested",
        "validation_failed",
    ]
    person: Person | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    data_request: DataRequest | None = None
    derivative: DerivativeDatasetRef | None = None
    message: str = ""
    errors: list[str] = Field(default_factory=list)


class MyceliumGraphState(BaseModel):
    """LangGraph state for orchestrator + specialist agents."""

    query: PersonQuery
    route: Literal["enrich", "validator", "finish"] | None = None
    response: PersonResponse | None = None
    person: Person | None = None
    derivative: DerivativeDatasetRef | None = None
    validation_passed: bool | None = None
    validation_errors: Annotated[list[str], operator.add] = Field(default_factory=list)
    audit_log: Annotated[list[str], operator.add] = Field(default_factory=list)


def attributes_requiring_derivative(requested: list[str]) -> list[str]:
    """Return requested attribute names that need a derivative dataset."""
    normalized = [a.strip().lower() for a in requested if a.strip()]
    return [
        attr
        for attr in normalized
        if attr in DERIVATIVE_ONLY_ATTRIBUTES
        or attr not in {f.lower() for f in CORE_PERSON_FIELDS}
    ]

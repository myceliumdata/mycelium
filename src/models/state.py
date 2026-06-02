"""Pydantic models for graph state, people queries, and JSON responses."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

# Strictly minimal core person fields (see docs/architecture.md)
CORE_PERSON_FIELDS: frozenset[str] = frozenset({"id", "name", "employer"})

MINIMUM_VIABLE_FIELDS: list[str] = ["name", "employer"]


class Person(BaseModel):
    """Core CRM person record — id, name, employer only.

    When supplying via `PersonQuery.provided_data` for an ingest/add:
    - You only need to provide `name` and `employer` (the minimum viable fields).
    - `id` can be "" (empty string) or omitted — it will be auto-generated
      by the enrich step as `person-{name-slug}-{6hex}`.
    - This is why `id` is NOT in MINIMUM_VIABLE_FIELDS and why the Studio
      input form no longer marks it as required (after the recent model fix).
    """

    id: str = ""
    name: str
    employer: str | None = None

    def core_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class PersonQuery(BaseModel):
    """Inbound JSON query for looking up a person (public interface).

    This model is query-only for the public interface (CLI, MCP, Studio).
    Data addition support will be re-introduced later via internal agent coordination.

    When using LangGraph Studio's visual input editor:
    - Provide a full ``MyceliumGraphState`` dict with a ``query`` key.
    - Set ``person_key`` (id or name) and optional ``requested_attributes``.
    - Set ``thread_id`` in Studio's Thread/Config panel, not in ``PersonQuery``.
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "person_key": "Nichanan Kesonpat",
                    "requested_attributes": [],
                },
                {
                    "person_key": "Nichanan Kesonpat",
                    "requested_attributes": ["email", "x_handle"],
                },
            ]
        }
    }

    person_key: str = Field(
        description="Person id or name used for core lookup.",
    )
    requested_attributes: list[str] = Field(
        default_factory=list,
        description="Non-core attributes requested; routed to specialist agents later.",
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
    """LangGraph state for supervisor + specialist agents.

    In LangGraph Studio (visual editor or JSON input):
    - You must provide at least the top-level "query" key (a PersonQuery).
    - Everything else (route, person, response, etc.) is internal state
      produced by the graph — do not set them in the initial input.
    - Use the examples in PersonQuery (they will appear in Studio).
    - For thread persistence in Studio, set the thread ID in the
      Studio UI's Thread/Config panel (it flows into invocation_thread_id).
    """

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

"""Pydantic models for graph state, people queries, and JSON responses."""

from __future__ import annotations

import operator
from typing import Annotated, Any

from pydantic import BaseModel, Field

class Person(BaseModel):
    """Identity record from seed (``data/seed.json``).

    ``id`` and ``person_id`` are the stable UUID from the seed loader (slice 1720).
    ``name`` and ``employer`` live in the seed but may be overridden by specialists.
    """

    id: str = ""
    person_id: str = ""
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
        description="Person UUID (person_id) or name used for seed lookup.",
    )
    requested_attributes: list[str] = Field(
        default_factory=list,
        description=(
            "Attributes requested (including name, employer); classified and "
            "routed to specialist agents when present."
        ),
    )


class PersonResponse(BaseModel):
    """Lightweight response for external consumers (CLI + MCP agents)."""

    results: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Identity records as plain dicts (id and person_id are the seed-loader "
            "UUID; name, employer). Always a list."
        ),
    )
    message: str = Field(
        default="",
        description=(
            "Human- and agent-readable narrative. Primary channel for state, "
            "progress, and reasoning."
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
    - Everything else (route, person, persons, response, etc.) is internal state
      produced by the graph — do not set them in the initial input.
    - ``persons`` holds all matches for a lookup; ``person`` is set only when
      exactly one match exists (name ambiguity may yield multiple ``persons``).
    - ``matched_persons``, ``context``, ``current_person_id``, and ``target_fields``
      are internal bags for the seed-data-context redesign (visible in Studio/LangSmith
      for debugging; populated by supervisor/context logic in later slices).
    - Use the examples in PersonQuery (they will appear in Studio).
    - For thread persistence in Studio, set the thread ID in the
      Studio UI's Thread/Config panel (it flows into invocation_thread_id).
    """

    query: PersonQuery
    route: str | None = Field(
        default=None,
        description=(
            'Target specialist name (e.g. "contact_specialist"). '
            "Set by supervisor; used by dispatch to invoke the registered agent. "
            "Phase 2+ dynamic."
        ),
    )
    response: PersonResponse | None = None
    person: Person | None = None
    persons: list[Person] = Field(default_factory=list)
    classifications: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Per-attribute classification metadata from supervisor "
            "(category, assigned_agent, confidence, ...). Phase 1 lookup only."
        ),
    )
    # Context / person_id fields added in the seed-data-context redesign
    # (see RESTART_PROMPT_FOR_PLAN.md and docs/plans/seed-data-context-architecture.md).
    # These are the mechanism by which the supervisor passes seed + cross-specialist
    # data to specialists.
    # TODO (future): specialists retrieve needed context from peers instead of
    # supervisor providing the full union.
    matched_persons: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Enriched seed records for matched person(s), including person_id "
            "from the seed loader."
        ),
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Supervisor-built context for matched person(s): "
            "{'seed': {...}, 'specialists': {'contact': {...}, ...}}. "
            "Specialist values override seed."
        ),
    )
    current_person_id: str | None = Field(
        default=None,
        description="Stable person_id for the specialist invocation path.",
    )
    target_fields: list[str] = Field(
        default_factory=list,
        description="Attributes the invoked specialist owns for this query.",
    )
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


def normalized_requested_attributes(requested: list[str]) -> list[str]:
    """Return trimmed, lowercased requested attribute names (empty strings dropped)."""
    return [a.strip().lower() for a in requested if a.strip()]

"""Pydantic models for graph state, entity queries, and JSON responses."""

from __future__ import annotations

import operator
from typing import Annotated, Any

from pydantic import BaseModel, Field


class SeedRecord(BaseModel):
    """Identity record from seed (``<network_root>/seed.json``).

    ``id`` is the stable UUID from the seed loader.
    ``name`` and ``employer`` live in the seed but may be overridden by specialists.
    """

    id: str = ""
    name: str
    employer: str | None = None

    def core_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class EntityKeySuggestion(BaseModel):
    """Near-miss seed name suggestion when entity_key has no exact match."""

    entity_key: str = Field(
        description="Retry key — seed display name (canonical for re-query).",
    )
    id: str = Field(description="Stable seed UUID for the suggested record.")
    name: str
    employer: str | None = None
    score: float = Field(description="Similarity score 0.0–1.0 (sequence_ratio).")
    reason: str = Field(
        default="sequence_ratio",
        description="Why this candidate was suggested (slice 1: sequence_ratio only).",
    )


class EntityQuery(BaseModel):
    """Inbound JSON query for looking up a seed record (public interface).

    This model is query-only for the public interface (CLI, MCP, Studio).
    Data addition support will be re-introduced later via internal agent coordination.

    When using LangGraph Studio's visual input editor:
    - Provide a full ``MyceliumGraphState`` dict with a ``query`` key.
    - Set ``entity_key`` (id or name) and optional ``requested_attributes``.
    - Set ``thread_id`` in Studio's Thread/Config panel, not in ``EntityQuery``.
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entity_key": "Nichanan Kesonpat",
                    "requested_attributes": [],
                },
                {
                    "entity_key": "Nichanan Kesonpat",
                    "requested_attributes": ["email", "x_handle"],
                },
            ]
        }
    }

    entity_key: str = Field(
        description="Seed record UUID (``id``) or display name used for lookup.",
    )
    binding: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Optional MVR bind fields (e.g. employer). Name comes from entity_key "
            "when network mvr.name_source is entity_key. Used to bind unknown entities."
        ),
    )
    requested_attributes: list[str] = Field(
        default_factory=list,
        description=(
            "Attributes requested (including name, employer); classified and "
            "routed to specialist agents when present."
        ),
    )


class QueryResponse(BaseModel):
    """Lightweight response for external consumers (CLI + MCP agents)."""

    outcome: str | None = Field(
        default=None,
        description=(
            "Machine-readable query outcome on every response: found (seed identity only), "
            "assembled (requested attributes merged), not_found, entity_key_unresolved "
            "(near-miss suggestions), entity_unknown (no seed match, MVR fields needed), "
            "entity_under_specified (partial binding), entity_bound_provisional "
            "(new registry bind), entity_validated (MVR validation passed), "
            "or error (internal failure). Mirrors debug outcome=."
        ),
    )
    required_fields: list[str] = Field(
        default_factory=list,
        description=(
            "MVR bind fields still needed when outcome is entity_unknown or "
            "entity_under_specified (excludes name when name_source is entity_key)."
        ),
    )
    suggestions: list[EntityKeySuggestion] = Field(
        default_factory=list,
        description=(
            "Near-miss entity_key suggestions when outcome is entity_key_unresolved; "
            "empty otherwise. Re-query with suggestions[].entity_key to confirm."
        ),
    )
    results: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Plain dicts per matched seed record. Always includes id (stable UUID). "
            "With no requested_attributes: id, name, employer. "
            "With requested_attributes: id plus only those keys after merge."
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
    - You must provide at least the top-level "query" key (an EntityQuery).
    - Everything else (route, seed_record, seed_records, response, etc.) is internal state
      produced by the graph — do not set them in the initial input.
    - ``seed_records`` holds all matches for a lookup; ``seed_record`` is set only when
      exactly one match exists (name ambiguity may yield multiple ``seed_records``).
    - ``matched_records``, ``context``, ``current_id``, and ``target_fields``
      are internal bags for the seed-data-context redesign (visible in Studio/LangSmith
      for debugging; populated by supervisor/context logic in later slices).
    - Use the examples in EntityQuery (they will appear in Studio).
    - For thread persistence in Studio, set the thread ID in the
      Studio UI's Thread/Config panel (it flows into invocation_thread_id).
    """

    query: EntityQuery
    route: str | None = Field(
        default=None,
        description=(
            'Target specialist name (e.g. "contact_specialist"). '
            "Set by supervisor; used by dispatch to invoke the registered agent. "
            "Phase 2+ dynamic."
        ),
    )
    response: QueryResponse | None = None
    seed_record: SeedRecord | None = None
    seed_records: list[SeedRecord] = Field(default_factory=list)
    classifications: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Per-attribute classification metadata from supervisor "
            "(category, assigned_agent, confidence, ...). Phase 1 lookup only."
        ),
    )
    # Context / id fields added in the seed-data-context redesign
    # (see RESTART_PROMPT_FOR_PLAN.md and docs/plans/seed-data-context-architecture.md).
    # These are the mechanism by which the supervisor passes seed + cross-specialist
    # data to specialists.
    # TODO (future): specialists retrieve needed context from peers instead of
    # supervisor providing the full union.
    matched_records: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Enriched seed records for matched entity lookup, including id "
            "from the seed loader."
        ),
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Supervisor-built context for matched record(s): "
            "{'seed': {...}, 'specialists': {'contact': {...}, ...}}. "
            "Specialist values override seed."
        ),
    )
    current_id: str | None = Field(
        default=None,
        description="Stable id (UUID) for the specialist invocation path.",
    )
    target_fields: list[str] = Field(
        default_factory=list,
        description="Attributes the invoked specialist owns for this query.",
    )
    validation_passed: bool | None = None
    validation_errors: Annotated[list[str], operator.add] = Field(default_factory=list)
    validation_contributions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Demographic/professional validation_contrib rows from validate_entity.",
    )
    audit_log: Annotated[list[str], operator.add] = Field(default_factory=list)
    invocation_thread_id: str | None = Field(
        default=None,
        description="Conversation thread id propagated into QueryResponse (set by run_query).",
    )
    invocation_trace_id: str | None = Field(
        default=None,
        description="LangSmith trace id propagated into QueryResponse (set by run_query).",
    )
    entity_resolution_kind: str | None = Field(
        default=None,
        description=(
            "Internal resolution kind: exact, multiple, suggest, unknown, "
            "under_specified, bind_provisional, or none."
        ),
    )
    entity_suggestions: list[EntityKeySuggestion] = Field(
        default_factory=list,
        description="Populated when entity_resolution_kind is suggest.",
    )
    entity_required_fields: list[str] = Field(
        default_factory=list,
        description="MVR gaps when entity_resolution_kind is unknown or under_specified.",
    )
    registry_provisional_only: bool = Field(
        default=False,
        description=(
            "When true, assemble identity-only response for provisional registry "
            "matches (no specialist research until validation gate)."
        ),
    )
    duplicate_bind: bool = Field(
        default=False,
        description="True when bind_index matched an existing provisional entity.",
    )


def normalized_requested_attributes(requested: list[str]) -> list[str]:
    """Return trimmed, lowercased requested attribute names (empty strings dropped)."""
    return [a.strip().lower() for a in requested if a.strip()]

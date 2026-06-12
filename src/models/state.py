"""Pydantic models for graph state, entity queries, and JSON responses."""

from __future__ import annotations

import operator
from typing import Annotated, Any

from pydantic import BaseModel, Field


class IdentityRecord(BaseModel):
    """Registry identity record (``id``, ``name``, ``employer``).

    ``id`` is the stable UUID from ``entities.json`` (assigned on import).
    ``name`` and ``employer`` may be overridden by specialists.
    """

    id: str = ""
    name: str
    employer: str | None = None

    def core_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class EntityKeySuggestion(BaseModel):
    """Near-miss registry name suggestion when entity_key has no exact match."""

    entity_key: str = Field(
        description="Retry key — registry display name (canonical for re-query).",
    )
    id: str = Field(description="Stable registry UUID for the suggested record.")
    name: str
    employer: str | None = None
    score: float = Field(description="Similarity score 0.0–1.0 (sequence_ratio).")
    reason: str = Field(
        default="sequence_ratio",
        description="Why this candidate was suggested (slice 1: sequence_ratio only).",
    )


class BillingPrincipal(BaseModel):
    """Optional billing identity for sponsor/pool funding models."""

    kind: str = Field(description="wallet | tenant | sponsor_id")
    id: str = Field(description="Principal identifier for entitlement attribution.")


class EntityQuery(BaseModel):
    """Inbound JSON query for looking up an entity (public interface).

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
        description="Registry entity UUID (``id``) or display name used for lookup.",
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
    quote_id: str | None = Field(
        default=None,
        description="Accepted quote id from a prior quote_required response (Slice 10).",
    )
    principal: BillingPrincipal | None = Field(
        default=None,
        description="Optional billing principal; required for some funding models.",
    )
    provenance: bool = Field(
        default=False,
        description=(
            "When true, request query delivery with sources/audit trail "
            "(metering: query_provenance consumption line)."
        ),
    )


class QueryResponse(BaseModel):
    """Lightweight response for external consumers (CLI + MCP agents)."""

    outcome: str | None = Field(
        default=None,
        description=(
            "Machine-readable query outcome on every response: found (registry identity only), "
            "assembled (requested attributes merged), not_found, entity_key_unresolved "
            "(near-miss suggestions), entity_unknown (no registry match, MVR fields needed), "
            "entity_under_specified (partial binding), entity_bound_provisional "
            "(new registry bind), entity_validated (MVR validation passed), "
            "quote_required (metering: accept quote before research/delivery), "
            "payment_required (metering: pay_quote before quote_id unlocks work), "
            "principal_required (metering: billing principal missing for funding model), "
            "or error (internal failure). Mirrors debug outcome=."
        ),
    )
    quote: dict[str, Any] | None = Field(
        default=None,
        description="Structured quote payload when outcome is quote_required or payment_required.",
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
            "Plain dicts per matched registry entity. Always includes id (stable UUID). "
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
    provenance: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Structured attribute versions when query.provenance=true; "
            "omitted or null otherwise."
        ),
    )


class MyceliumGraphState(BaseModel):
    """LangGraph state for supervisor + specialist agents.

    In LangGraph Studio (visual editor or JSON input):
    - You must provide at least the top-level "query" key (an EntityQuery).
    - Everything else (route, identity_record, identity_records, response, etc.) is internal state
      produced by the graph — do not set them in the initial input.
    - ``matched_records`` is the canonical registry match list (dict rows).
    - ``identity_records`` / ``identity_record`` are optional typed mirrors for Studio
      (specialists may set ``identity_record`` when a single match is resolved).
    - ``matched_records``, ``context``, ``current_id``, and ``target_fields``
      are internal bags for context assembly (visible in Studio/LangSmith for debugging).
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
    identity_record: IdentityRecord | None = None
    identity_records: list[IdentityRecord] = Field(default_factory=list)
    classifications: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Per-attribute classification metadata from supervisor "
            "(category, assigned_agent, confidence, ...). Phase 1 lookup only."
        ),
    )
    # Context / id fields added in the seed-data-context redesign
    # (see RESTART_PROMPT_FOR_PLAN.md and docs/plans/seed-data-context-architecture.md).
    # These are the mechanism by which the supervisor passes identity + cross-specialist
    # data to specialists.
    # TODO (future): specialists retrieve needed context from peers instead of
    # supervisor providing the full union.
    matched_records: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Registry match rows for the current lookup, including stable id."
        ),
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Supervisor-built context for matched record(s): "
            "{'entity_id', 'bind', 'specialists': {...}, '_meta': {...}}. "
            "Specialist values override bind fields when requested."
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
    duplicate_bind: bool = Field(
        default=False,
        description="True when bind_index matched an existing provisional entity.",
    )
    pending_quote: dict[str, Any] | None = Field(
        default=None,
        description="Quote awaiting acceptance when metering gate blocks progress.",
    )
    metering_accepted_quote: dict[str, Any] | None = Field(
        default=None,
        description="Accepted quote payload for this invocation (internal).",
    )
    metering_write_entitlement: bool = Field(
        default=False,
        description="Write entitlement after successful production research this pass.",
    )
    metering_principal_required: str | None = Field(
        default=None,
        description="Funding model name when billing principal is required but missing.",
    )
    metering_payment_required: bool = Field(
        default=False,
        description="True when quote_id was supplied but quote is not paid yet.",
    )


def normalized_requested_attributes(requested: list[str]) -> list[str]:
    """Return trimmed, lowercased requested attribute names (empty strings dropped)."""
    return [a.strip().lower() for a in requested if a.strip()]

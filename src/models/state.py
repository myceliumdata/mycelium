"""Pydantic models for graph state, entity queries, and JSON responses."""

from __future__ import annotations

import operator
import os
from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator


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


class DeliveryPayload(BaseModel):
    """Step-1 delivery token returned when lookup resolves."""

    delivery_id: str = Field(description="Opaque delivery scope id from step 1 (d_ prefix).")
    expires_at: str = Field(description="ISO-8601 expiry for delivery_id (default TTL 5 minutes).")
    create_on_deliver: bool | None = Field(
        default=None,
        description=(
            "Present and true only when step 2 will create a provisional entity from "
            "step-1 lookup (0 registry matches, full MVR). Omitted for existing matches."
        ),
    )

    @classmethod
    def from_scope(cls, scope: Any) -> DeliveryPayload:
        """Build a step-1 delivery payload from a persisted ``DeliveryScope``."""
        payload = cls(
            delivery_id=scope.delivery_id,
            expires_at=scope.expires_at,
        )
        if scope.create_on_deliver:
            return payload.model_copy(update={"create_on_deliver": True})
        return payload


class EntityQuery(BaseModel):
    """Inbound JSON query for looking up an entity (public interface).

    This model is query-only for the public interface (CLI, MCP, Studio).
    Data addition support will be re-introduced later via internal agent coordination.

    When using LangGraph Studio's visual input editor:
    - Provide a full ``MyceliumGraphState`` dict with a ``query`` key.
    - Set ``lookup`` or ``id`` (step 1) or ``delivery_id`` (step 2) and optional ``requested_attributes``.
    - Set ``thread_id`` in Studio's Thread/Config panel, not in ``EntityQuery``.
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "lookup": {"employer": "645 Ventures"},
                    "requested_attributes": ["email"],
                },
                {
                    "delivery_id": "d_abc123",
                    "quote_id": "q_xyz789",
                },
            ]
        }
    }

    id: str | None = Field(
        default=None,
        description=(
            "Step 1: stable registry entity UUID (not delivery_id or quote_id). "
            "Returns delivery_id for step 2."
        ),
    )
    lookup: dict[str, str] = Field(
        default_factory=dict,
        description="Step 1: partial field match map (AND within keys); keys ⊆ mvr.bind_fields.",
    )
    delivery_id: str | None = Field(
        default=None,
        description="Step 2: delivery scope id from a prior lookup_resolved response.",
    )
    entity_key: str = Field(
        default="",
        description=(
            "Deprecated legacy resolve key (registry UUID or display name). "
            "Public CLI/MCP/admin reject this (M9); internal graph tests may still use it."
        ),
    )
    binding: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Deprecated legacy MVR bind fields (e.g. employer). "
            "Prefer lookup for step 1; used with entity_key until M4."
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
            "Step 1 only. When true, request query delivery with sources/audit trail "
            "(metering: query_provenance consumption line)."
        ),
    )

    @model_validator(mode="after")
    def _validate_target_protocol_step(self) -> EntityQuery:
        delivery_id = (self.delivery_id or "").strip()
        if delivery_id:
            if (self.entity_key or "").strip():
                raise ValueError("step 2 accepts only delivery_id")
            if self.lookup:
                raise ValueError("step 2 accepts only delivery_id")
            if (self.id or "").strip():
                raise ValueError("step 2 accepts only delivery_id")
            if self.binding:
                raise ValueError("step 2 accepts only delivery_id")
            if self.requested_attributes:
                raise ValueError("requested_attributes are step 1 only")
            if self.provenance:
                raise ValueError("provenance is step 1 only")
            if self.principal is not None:
                raise ValueError("step 2 accepts only delivery_id")
            return self

        has_id = bool((self.id or "").strip())
        has_lookup = bool(self.lookup)
        has_entity_key = bool(self.entity_key)
        if not (has_id or has_lookup or has_entity_key):
            raise ValueError("step 1 requires id, lookup, or entity_key")
        return self


def entity_query_is_delivery_step(query: EntityQuery) -> bool:
    """Return True when the query is step 2 (deliver via delivery_id)."""
    return bool((query.delivery_id or "").strip())


def entity_query_is_target_resolve_step(query: EntityQuery) -> bool:
    """Return True for step-1 target protocol (id or lookup), not legacy entity_key."""
    if entity_query_is_delivery_step(query):
        return False
    return bool((query.id or "").strip()) or bool(query.lookup)


def entity_query_is_legacy_entity_key_step(query: EntityQuery) -> bool:
    """Return True for deprecated step-1 entity_key resolution (internal tests only)."""
    if entity_query_is_delivery_step(query) or entity_query_is_target_resolve_step(query):
        return False
    return bool((query.entity_key or "").strip())


def legacy_entity_key_allowed() -> bool:
    """True when MYCELIUM_ALLOW_LEGACY_ENTITY_KEY enables internal graph tests."""
    return os.getenv("MYCELIUM_ALLOW_LEGACY_ENTITY_KEY", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


class QueryResponse(BaseModel):
    """Lightweight response for external consumers (CLI + MCP agents)."""

    outcome: str | None = Field(
        default=None,
        description=(
            "Machine-readable query outcome on every response: lookup_resolved (step 1; "
            "total_matches + delivery_id), found (registry identity only), "
            "assembled (requested attributes merged), not_found, "
            "quote_required (metering: accept quote before research/delivery), "
            "payment_required (metering: pay_quote before quote_id unlocks work), "
            "principal_required (metering: billing principal missing for funding model), "
            "or error (internal failure). Legacy outcomes (entity_key_unresolved, "
            "entity_unknown, entity_bound_provisional, …) remain for internal "
            "entity_key graph tests only. Mirrors debug outcome=."
        ),
    )
    total_matches: int | None = Field(
        default=None,
        description="Step 1 lookup_resolved: number of registry rows matching the lookup.",
    )
    delivery: DeliveryPayload | None = Field(
        default=None,
        description="Step 1 lookup_resolved: delivery_id + expires_at for step-2 deliver.",
    )
    quote: dict[str, Any] | None = Field(
        default=None,
        description="Structured quote payload when outcome is quote_required or payment_required.",
    )
    required_fields: list[str] = Field(
        default_factory=list,
        description=(
            "MVR bind fields still needed when outcome is entity_unknown or "
            "entity_under_specified (legacy entity_key path; name may come from entity_key)."
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

    def public_dict(self) -> dict[str, Any]:
        """Serialize for CLI, MCP, and admin — omit null optional fields."""
        return self.model_dump(exclude_none=True)

    def public_json(self, *, indent: int | None = 2) -> str:
        """JSON for public surfaces; omits null optional fields (e.g. create_on_deliver)."""
        return self.model_dump_json(exclude_none=True, indent=indent)


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
    delivery_scope_attrs: list[str] = Field(
        default_factory=list,
        description=(
            "Step-2 deliver: requested_attributes bound on step-1 delivery scope "
            "(internal; not sent on public EntityQuery)."
        ),
    )
    delivery_scope_provenance: bool = Field(
        default=False,
        description="Step-2 deliver: provenance flag bound on step-1 delivery scope.",
    )


def graph_requested_attributes(state: MyceliumGraphState) -> list[str]:
    """Attrs to execute for this graph turn (step-2 scope or query step-1)."""
    if state.delivery_scope_attrs:
        return normalized_requested_attributes(state.delivery_scope_attrs)
    return normalized_requested_attributes(state.query.requested_attributes)


def graph_provenance_requested(state: MyceliumGraphState) -> bool:
    """Whether provenance delivery was requested (step-2 scope or query)."""
    if state.delivery_scope_attrs or state.delivery_scope_provenance:
        return state.delivery_scope_provenance
    return bool(state.query.provenance)


def normalized_requested_attributes(requested: list[str]) -> list[str]:
    """Return trimmed, lowercased requested attribute names (empty strings dropped)."""
    return [a.strip().lower() for a in requested if a.strip()]

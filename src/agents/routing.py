"""Supervisor routing decisions: classify queries and delegate data access."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agents.entity_resolution import lookup_entities_by_key
from agents.responses import response_found, response_non_core, response_not_found
from models.state import (
    MyceliumGraphState,
    QueryResponse,
    SeedRecord,
    normalized_requested_attributes,
)


@dataclass(frozen=True)
class SupervisorDecision:
    """Outcome of one supervisor evaluation turn (query-only public paths)."""

    response: QueryResponse
    seed_records: list[SeedRecord] = field(default_factory=list)
    seed_record: SeedRecord | None = None
    thread_id: str | None = None
    trace_id: str | None = None


def _resolve_invocation_ids(
    state: MyceliumGraphState,
    *,
    thread_id: str | None,
    trace_id: str | None,
) -> tuple[str | None, str | None]:
    """Prefer explicit parameters, then values already on graph state."""
    resolved_thread = thread_id if thread_id is not None else state.invocation_thread_id
    resolved_trace = trace_id if trace_id is not None else state.invocation_trace_id
    return resolved_thread, resolved_trace


def _rows_to_seed_records(rows: list[dict[str, Any]]) -> list[SeedRecord]:
    return [
        SeedRecord(
            id=str(row.get("id") or ""),
            name=str(row.get("name") or ""),
            employer=row.get("employer"),
        )
        for row in rows
        if isinstance(row, dict)
    ]


def evaluate_supervisor_turn(
    state: MyceliumGraphState,
    *,
    entity_lookup: Callable[[str], list[dict[str, Any]]] | None = None,
    seed_lookup: Callable[[str], list[dict[str, Any]]] | None = None,
    thread_id: str | None = None,
    trace_id: str | None = None,
) -> SupervisorDecision:
    """
    Classify a query-only request and build the appropriate QueryResponse.

    Entity lookups use ``lookup_entities_by_key``; this function only coordinates
    routing and selects response shapes (found, not-found, non-core).
    """
    lookup = entity_lookup or seed_lookup or lookup_entities_by_key
    query = state.query
    resolved_thread_id, resolved_trace_id = _resolve_invocation_ids(
        state,
        thread_id=thread_id,
        trace_id=trace_id,
    )
    id_kwargs = {
        "thread_id": resolved_thread_id,
        "trace_id": resolved_trace_id,
    }

    seed_records = _rows_to_seed_records(lookup(query.entity_key))
    if not seed_records:
        return SupervisorDecision(
            response=response_not_found(query, **id_kwargs),
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    single = seed_records[0] if len(seed_records) == 1 else None
    requested = normalized_requested_attributes(query.requested_attributes)
    if requested:
        return SupervisorDecision(
            response=response_non_core(query, seed_records, requested, **id_kwargs),
            seed_records=seed_records,
            seed_record=single,
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    return SupervisorDecision(
        response=response_found(query, seed_records, **id_kwargs),
        seed_records=seed_records,
        seed_record=single,
        thread_id=resolved_thread_id,
        trace_id=resolved_trace_id,
    )

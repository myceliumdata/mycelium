"""Supervisor routing decisions: classify queries and delegate data access."""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.core_identity import CoreIdentity, get_core_identity
from agents.responses import response_found, response_non_core, response_not_found
from models.state import (
    MyceliumGraphState,
    Person,
    PersonResponse,
    normalized_requested_attributes,
)


@dataclass(frozen=True)
class SupervisorDecision:
    """Outcome of one supervisor evaluation turn (query-only public paths)."""

    response: PersonResponse
    persons: list[Person] = field(default_factory=list)
    person: Person | None = None
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


def evaluate_supervisor_turn(
    state: MyceliumGraphState,
    *,
    core_identity: CoreIdentity | None = None,
    thread_id: str | None = None,
    trace_id: str | None = None,
) -> SupervisorDecision:
    """
    Classify a query-only request and build the appropriate PersonResponse.

    Core lookups are delegated to ``CoreIdentity``; this function only coordinates
    routing and selects response shapes (found, not-found, non-core).
    """
    core_identity = core_identity or get_core_identity()
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

    persons = core_identity.find_by_key(query.person_key)
    if not persons:
        return SupervisorDecision(
            response=response_not_found(query, **id_kwargs),
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    single = persons[0] if len(persons) == 1 else None
    requested = normalized_requested_attributes(query.requested_attributes)
    if requested:
        return SupervisorDecision(
            response=response_non_core(query, persons, requested, **id_kwargs),
            persons=persons,
            person=single,
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    return SupervisorDecision(
        response=response_found(query, persons, **id_kwargs),
        persons=persons,
        person=single,
        thread_id=resolved_thread_id,
        trace_id=resolved_trace_id,
    )

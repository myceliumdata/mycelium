"""Supervisor routing decisions: classify requests and delegate data access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agents.core_identity import CoreIdentity, get_core_identity
from agents.responses import (
    response_found,
    response_ingest_failure,
    response_ingest_success,
    response_non_core,
    response_not_found,
)
from models.state import MyceliumGraphState, Person, PersonResponse, non_core_attributes


@dataclass(frozen=True)
class SupervisorDecision:
    """Outcome of one supervisor evaluation turn."""

    action: Literal["respond", "route_enrich"]
    response: PersonResponse | None = None
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
    Classify the current graph state and decide how the supervisor should proceed.

    Data access (find/persist) is delegated to ``CoreIdentity``; this function only
    coordinates routing and selects response shapes.
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

    if state.validation_passed is False:
        error_summary = "; ".join(state.validation_errors) or "unknown validation errors"
        return SupervisorDecision(
            action="respond",
            response=response_ingest_failure(query, error_summary, **id_kwargs),
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    if state.validation_passed is True and state.person is not None:
        core_identity.persist(state.person)
        return SupervisorDecision(
            action="respond",
            response=response_ingest_success(query, state.person, **id_kwargs),
            person=state.person,
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    if query.provided_data is not None:
        return SupervisorDecision(
            action="route_enrich",
            person=query.provided_data,
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    person = core_identity.find_by_key(query.person_key)
    if person is None:
        return SupervisorDecision(
            action="respond",
            response=response_not_found(query, **id_kwargs),
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    deferred = non_core_attributes(query.requested_attributes)
    if deferred:
        return SupervisorDecision(
            action="respond",
            response=response_non_core(query, person, deferred, **id_kwargs),
            person=person,
            thread_id=resolved_thread_id,
            trace_id=resolved_trace_id,
        )

    return SupervisorDecision(
        action="respond",
        response=response_found(query, person, **id_kwargs),
        person=person,
        thread_id=resolved_thread_id,
        trace_id=resolved_trace_id,
    )

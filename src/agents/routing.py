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


def evaluate_supervisor_turn(
    state: MyceliumGraphState,
    *,
    identity: CoreIdentity | None = None,
) -> SupervisorDecision:
    """
    Classify the current graph state and decide how the supervisor should proceed.

    Data access (find/persist) is delegated to ``CoreIdentity``; this function only
    coordinates routing and selects response shapes.
    """
    core_identity = identity or get_core_identity()
    query = state.query

    if state.validation_passed is False:
        error_summary = "; ".join(state.validation_errors) or "unknown validation errors"
        return SupervisorDecision(
            action="respond",
            response=response_ingest_failure(query, error_summary),
        )

    if state.validation_passed is True and state.person is not None:
        core_identity.persist(state.person)
        return SupervisorDecision(
            action="respond",
            response=response_ingest_success(query, state.person),
            person=state.person,
        )

    if query.provided_data is not None:
        return SupervisorDecision(
            action="route_enrich",
            person=query.provided_data,
        )

    person = core_identity.find_by_key(query.person_key)
    if person is None:
        return SupervisorDecision(
            action="respond",
            response=response_not_found(query),
        )

    deferred = non_core_attributes(query.requested_attributes)
    if deferred:
        return SupervisorDecision(
            action="respond",
            response=response_non_core(query, person, deferred),
            person=person,
        )

    return SupervisorDecision(
        action="respond",
        response=response_found(query, person),
        person=person,
    )

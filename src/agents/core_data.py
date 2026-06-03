"""Core Data specialist agent — owns core person lookups (id, name, employer)."""

from __future__ import annotations

from typing import Any

from agents.core_identity import CoreIdentity, get_core_identity
from agents.responses import response_found, response_non_core, response_not_found
from models.state import MyceliumGraphState, Person, PersonResponse, non_core_attributes


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _resolve_invocation_ids(state: MyceliumGraphState) -> tuple[str | None, str | None]:
    return state.invocation_thread_id, state.invocation_trace_id


def _build_lookup_response(
    state: MyceliumGraphState,
    *,
    core_identity: CoreIdentity,
) -> tuple[list[Person], PersonResponse, str]:
    """
    Perform a core lookup and select the query response shape.

    Returns (matched persons, response, audit outcome tag).
    """
    query = state.query
    thread_id, trace_id = _resolve_invocation_ids(state)
    id_kwargs = {"thread_id": thread_id, "trace_id": trace_id}

    matches = core_identity.find_by_key(query.person_key)
    if not matches:
        return (
            [],
            response_not_found(query, **id_kwargs),
            "not_found",
        )

    deferred = non_core_attributes(query.requested_attributes)
    if deferred:
        return (
            matches,
            response_non_core(query, matches, deferred, **id_kwargs),
            "non_core_requested",
        )

    return (
        matches,
        response_found(query, matches, **id_kwargs),
        "found",
    )


def _run_core_data_lookup(
    state: MyceliumGraphState,
    *,
    core_identity: CoreIdentity | None = None,
) -> dict[str, Any]:
    """Synchronous lookup + response build (for asyncio.to_thread)."""
    identity = core_identity or get_core_identity()
    matches, response, outcome = _build_lookup_response(state, core_identity=identity)
    logs = [f"CoreDataAgent: lookup {outcome} for person_key={state.query.person_key!r}."]
    payload: dict[str, Any] = {
        "response": response,
        "route": None,
        "audit_log": logs,
        "persons": matches,
    }
    if len(matches) == 1:
        payload["person"] = matches[0]
    if state.invocation_thread_id is not None:
        payload["invocation_thread_id"] = state.invocation_thread_id
    if state.invocation_trace_id is not None:
        payload["invocation_trace_id"] = state.invocation_trace_id
    return payload


def core_data_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Specialist agent that owns core CRM data access for public queries.

    Resolves ``query.person_key`` via ``CoreIdentity``, then sets ``person`` and
    ``response`` on graph state (found, not-found, or non-core attribute narrative).
    Persist and other mutations will be added here later as internal coordination.

    This is a synchronous function so the compiled graph supports both
    graph.invoke() (used by the stable MCP server path) and ainvoke()
    (used by LangGraph Studio).
    """
    current = _coerce(state)
    return _run_core_data_lookup(current)

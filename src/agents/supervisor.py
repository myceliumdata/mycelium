"""Supervisor agent: coordinator and router for core lookup, ingest, and specialist handoff."""

from __future__ import annotations

import asyncio
from typing import Any

from agents.routing import SupervisorDecision, evaluate_supervisor_turn
from models.state import MyceliumGraphState


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _apply_decision(decision: SupervisorDecision) -> dict[str, Any]:
    logs: list[str] = []

    if decision.action == "route_enrich":
        logs.append("Supervisor: provided_data present — routing to enrich.")
        payload: dict[str, Any] = {
            "person": decision.person,
            "route": "enrich",
            "audit_log": logs,
        }
        if decision.thread_id is not None:
            payload["invocation_thread_id"] = decision.thread_id
        if decision.trace_id is not None:
            payload["invocation_trace_id"] = decision.trace_id
        return payload

    logs.append("Supervisor: responding — finishing.")
    payload = {
        "response": decision.response,
        "route": None,
        "audit_log": logs,
    }
    if decision.person is not None:
        payload["person"] = decision.person
    return payload


async def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Coordinator entry point: classify the request, delegate data work, route or respond.

    Does not call storage directly; see ``agents.routing`` and ``agents.core_identity``.
    Propagates ``invocation_thread_id`` / ``invocation_trace_id`` from state into responses.

    SQLite lookups/persistence run in a worker thread so ASGI servers stay non-blocking.
    """
    current = _coerce(state)
    decision = await asyncio.to_thread(
        evaluate_supervisor_turn,
        current,
        thread_id=current.invocation_thread_id,
        trace_id=current.invocation_trace_id,
    )
    result = _apply_decision(decision)
    result["audit_log"] = ["Supervisor: evaluating query.", *result.get("audit_log", [])]
    return result

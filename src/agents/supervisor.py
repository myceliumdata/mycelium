"""Supervisor agent: coordinator and router for core lookups and specialist handoff."""

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
    payload: dict[str, Any] = {
        "response": decision.response,
        "route": None,
        "audit_log": ["Supervisor: responding — query complete."],
    }
    if decision.person is not None:
        payload["person"] = decision.person
    if decision.thread_id is not None:
        payload["invocation_thread_id"] = decision.thread_id
    if decision.trace_id is not None:
        payload["invocation_trace_id"] = decision.trace_id
    return payload


async def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Coordinator entry point: classify the query, delegate lookup, and respond.

    Does not call storage directly; see ``agents.routing`` and ``agents.core_identity``.
    Propagates ``invocation_thread_id`` / ``invocation_trace_id`` into responses.

    SQLite lookups run in a worker thread so ASGI servers stay non-blocking.
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

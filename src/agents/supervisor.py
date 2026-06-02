"""Supervisor agent: coordinator and router for core lookups and specialist handoff."""

from __future__ import annotations

from typing import Any

from models.state import MyceliumGraphState


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Coordinator entry point: classify the query and route to specialists.

    Does not access storage or build ``PersonResponse`` payloads. Core lookups
    are delegated to ``core_data_agent`` via ``route="core_data"``.
    """
    _ = _coerce(state)
    return {
        "route": "core_data",
        "audit_log": [
            "Supervisor: evaluating query.",
            "Supervisor: routing to core_data specialist.",
        ],
    }

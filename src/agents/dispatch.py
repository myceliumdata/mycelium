"""Specialist dispatcher (routes state.route to the registry fn). See approved plan Step 5."""

from __future__ import annotations

from typing import Any

from agents.core_data import core_data_agent
from agents.registry import get_agent_registry
from models.state import MyceliumGraphState


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def specialist_dispatcher(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    current = _coerce(state)
    target = current.route or "core_data"
    fn = get_agent_registry().get_agent_fn(target)
    if fn is None:
        fn = core_data_agent
    return fn(current)

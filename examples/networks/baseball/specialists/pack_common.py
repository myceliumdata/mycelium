"""Shared graph helpers for baseball pack specialists (re-exports + legacy wrappers)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_bootstrap_path = Path(__file__).resolve().parent / "pack_bootstrap.py"
_bootstrap_spec = importlib.util.spec_from_file_location(
    "_baseball_pack_bootstrap",
    _bootstrap_path,
)
if _bootstrap_spec is None or _bootstrap_spec.loader is None:
    raise ImportError(f"Cannot load pack_bootstrap from {_bootstrap_path}")
_bootstrap_mod = importlib.util.module_from_spec(_bootstrap_spec)
_bootstrap_spec.loader.exec_module(_bootstrap_mod)
_bootstrap_mod.bootstrap(__file__)

from typing import Any, Callable

from agents.specialists.agent import SpecialistAgent
from agents.specialists.warehouse_stat import (
    WarehousePlayerStatSpecialist,
    WarehouseTeamStatSpecialist,
    coerce_state,
    identity_from_context,
    now_iso,
    overall_field_status,
    query_year_id,
    resolve_entity_id,
    resolve_owned_fields,
)
from models.state import MyceliumGraphState

from baseball_warehouse_hooks import LAHMAN_PLAYER_ID, LAHMAN_TEAM_ID

__all__ = [
    "LAHMAN_PLAYER_ID",
    "LAHMAN_TEAM_ID",
    "coerce_state",
    "identity_from_context",
    "now_iso",
    "overall_field_status",
    "query_year_id",
    "resolve_entity_id",
    "resolve_owned_fields",
    "run_warehouse_player_graph",
    "run_warehouse_team_graph",
]


def run_warehouse_player_graph(
    state: MyceliumGraphState | dict[str, Any],
    *,
    agent: SpecialistAgent,
    category: str,
    domain: str,
    on_miss: Callable[[str], bool] | None = None,
    on_miss_resolve: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Legacy wrapper — prefer ``WarehousePlayerStatSpecialist`` subclasses."""
    _ = on_miss, on_miss_resolve
    if isinstance(agent, WarehousePlayerStatSpecialist):
        return agent.run(state)
    raise TypeError(
        "run_warehouse_player_graph requires a WarehousePlayerStatSpecialist agent",
    )


def run_warehouse_team_graph(
    state: MyceliumGraphState | dict[str, Any],
    *,
    agent: SpecialistAgent,
    category: str,
    domain: str,
) -> dict[str, Any]:
    """Legacy wrapper — prefer ``WarehouseTeamStatSpecialist`` subclasses."""
    _ = category, domain
    if isinstance(agent, WarehouseTeamStatSpecialist):
        return agent.run(state)
    raise TypeError(
        "run_warehouse_team_graph requires a WarehouseTeamStatSpecialist agent",
    )

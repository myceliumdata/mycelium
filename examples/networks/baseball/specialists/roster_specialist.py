"""roster_specialist — team roster product (Appearances ⋈ People)."""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from typing import Any

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

from agents.specialists.agent import SpecialistAgent
from models.state import MyceliumGraphState
from network.paths import NetworkPaths

from product_common import (
    json_string_list,
    run_product_team_specialist,
    team_roster_names,
)
from specialist_loader import load_warehouse_resolve

ROSTER_INLINE = inspect.getsource(team_roster_names)


def _compute_roster(
    attr: str,
    *,
    team_id: str,
    warehouse: Path,
    year_id: str | None,
    paths: NetworkPaths,
) -> tuple[str | None, str, dict[str, str]]:
    _ = attr
    names = team_roster_names(team_id, warehouse, year_id=year_id)
    if not names:
        return None, ROSTER_INLINE, {}
    wr = load_warehouse_resolve()
    params = wr.team_provenance_parameters(
        team_id=team_id,
        paths=paths,
        warehouse=warehouse,
        attribute="roster",
        year_id=year_id,
    )
    return json_string_list(names), ROSTER_INLINE, params


class RosterSpecialist(SpecialistAgent):
    category = "team_roster"
    agent_name = "roster_specialist"

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        return run_product_team_specialist(
            state,
            agent=AGENT,
            category="team_roster",
            compute_attr=_compute_roster,
        )


AGENT = RosterSpecialist()


def roster_specialist(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return AGENT.run(state)

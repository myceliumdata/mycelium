"""team_season_specialist — warehouse-backed team season facts (baseball pack)."""

from __future__ import annotations

import importlib.util
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

from pack_common import run_warehouse_team_graph


class TeamSeasonSpecialist(SpecialistAgent):
    category = "team_season"
    agent_name = "team_season_specialist"

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        return run_warehouse_team_graph(
            state,
            agent=AGENT,
            category="team_season",
            domain="team_season",
        )


AGENT = TeamSeasonSpecialist()


def team_season_specialist(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return AGENT.run(state)
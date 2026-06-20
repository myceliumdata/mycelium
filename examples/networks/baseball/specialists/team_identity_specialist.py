"""team_identity_specialist — registry bind fields for team MVR (baseball pack)."""

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

from registry_identity_common import run_registry_identity_graph


class TeamIdentitySpecialist(SpecialistAgent):
    category = "team_identity"
    agent_name = "team_identity_specialist"

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        return run_registry_identity_graph(
            state,
            agent=AGENT,
            category="team_identity",
            record_type="team",
        )


AGENT = TeamIdentitySpecialist()


def team_identity_specialist(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return AGENT.run(state)
"""Baseball pack hooks for framework warehouse stat specialists."""

from __future__ import annotations

from typing import Any

from specialist_loader import load_derive_resolve, load_warehouse_resolve

LAHMAN_PLAYER_ID = "lahman.playerID"
LAHMAN_TEAM_ID = "lahman.teamID"


class BaseballWarehousePlayerHooks:
    player_source_key = LAHMAN_PLAYER_ID
    player_record_type = "player"

    def _load_warehouse_resolve(self) -> Any:
        return load_warehouse_resolve()

    def _load_derive_resolve(self) -> Any:
        return load_derive_resolve()


class BaseballWarehouseTeamHooks:
    team_source_key = LAHMAN_TEAM_ID
    team_record_type = "team"

    def _load_warehouse_resolve(self) -> Any:
        return load_warehouse_resolve()

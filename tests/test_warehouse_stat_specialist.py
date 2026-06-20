"""Tests for framework warehouse stat specialist bases."""

from __future__ import annotations

import pytest

from agents.specialists.warehouse_stat import (
    WarehousePlayerStatSpecialist,
    WarehouseTeamStatSpecialist,
)


class _StubPlayerStat(WarehousePlayerStatSpecialist):
    category = "batting"
    domain = "batting"
    agent_name = "stub_player_stat"
    player_source_key = "test.playerID"

    def _load_warehouse_resolve(self) -> object:
        return object()

    def _load_derive_resolve(self) -> object:
        return object()


class _StubTeamStat(WarehouseTeamStatSpecialist):
    category = "team_season"
    domain = "team_season"
    agent_name = "stub_team_stat"
    team_source_key = "test.teamID"

    def _load_warehouse_resolve(self) -> object:
        return object()


@pytest.mark.smoke
def test_derive_on_miss_enabled_from_manifest() -> None:
    agent = _StubPlayerStat()
    assert agent.derive_on_miss_enabled(
        {"domains": {"batting": {"derive_on_miss": True}}},
    )
    assert not agent.derive_on_miss_enabled(
        {"domains": {"batting": {"derive_on_miss": False}}},
    )
    assert not agent.derive_on_miss_enabled({"domains": {}})
    assert not agent.derive_on_miss_enabled(
        {"domains": {"pitching": {"derive_on_miss": True}}},
    )


@pytest.mark.smoke
def test_warehouse_player_stat_requires_resolver_hook() -> None:
    class _BarePlayer(WarehousePlayerStatSpecialist):
        category = "batting"
        domain = "batting"
        agent_name = "bare_player"
        player_source_key = "test.playerID"

    with pytest.raises(NotImplementedError):
        _BarePlayer()._load_warehouse_resolve()


@pytest.mark.smoke
def test_warehouse_team_stat_requires_resolver_hook() -> None:
    agent = _StubTeamStat()
    assert agent._load_warehouse_resolve() is not None

"""Tests for framework warehouse stat specialist bases."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.specialists.warehouse_stat import (
    WarehousePlayerStatSpecialist,
    WarehouseResearchStatSpecialist,
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


class _CapturingDerive:
    last_domain: str | None = None

    def generate_and_run_derive(self, attr, **kwargs):
        type(self).last_domain = kwargs.get("domain")

        class _Result:
            audit_log = ()
            field = None

        return _Result()


@pytest.mark.smoke
def test_resolve_derive_on_miss_passes_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = _StubPlayerStat()
    agent.domain = "pitching"
    capture = _CapturingDerive()
    monkeypatch.setattr(agent, "_load_derive_resolve", lambda: capture)
    monkeypatch.setattr(
        "network.intent_map.load_intent_map",
        lambda _paths: {},
    )
    monkeypatch.setattr(
        "network.intent_map.lookup_intent_slug",
        lambda key, _map: key,
    )
    from types import SimpleNamespace

    paths = SimpleNamespace(root=Path("/tmp/unused-mycelium-root"))
    manifest = {"domains": {"pitching": {"derive_on_miss": True}}}
    agent.resolve_derive_on_miss(
        "ent-1",
        "career_whip",
        record={},
        player_id="ryanno01",
        warehouse=paths.root / "warehouse" / "lahman.sqlite",
        manifest=manifest,
        paths=paths,
        sources=[],
        now="2026-01-01T00:00:00+00:00",
    )
    assert capture.last_domain == "pitching"


class _ResearchStub(WarehousePlayerStatSpecialist):
    category = "bio"
    domain = "bio"
    agent_name = "stub_bio"
    player_source_key = "test.playerID"
    research_calls: list[list[str]] = []

    def _load_warehouse_resolve(self) -> object:
        class _WR:
            @staticmethod
            def load_manifest(_paths):
                return {"domains": {"bio": {"research_on_miss": True}}}

            @staticmethod
            def domain_aliases(_manifest, _domain):
                return {"birth_date": {}}

        return _WR()

    def _load_derive_resolve(self) -> object:
        return object()

    def _run_research_on_miss(self, entity_id, need, ctx):
        type(self).research_calls.append(list(need))
        return ([f"{self.agent_name}: research stub"], [])


@pytest.mark.smoke
def test_research_on_miss_defers_unaliased_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BioResearch(_ResearchStub, WarehouseResearchStatSpecialist):
        pass

    agent = _BioResearch()
    manifest = {"domains": {"bio": {"research_on_miss": True}}}
    assert agent.defer_miss_to_research("primary_nickname", manifest)
    assert not agent.defer_miss_to_research("birth_date", manifest)

"""Smoke tests for multi-grain query router and delivery grain."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.entity_registry import RegistryEntity, get_entity_registry, reset_entity_registry
from agents.grain_disambiguation import GrainDisambiguationResult
from agents.query_grain_router import (
    fan_out_lookup,
    filter_lookup_for_grain,
    grains_with_filtered_lookup,
    resolve_id_all_grains,
    resolve_lookup_multi_grain,
)
from agents.target_deliver import load_delivery_scope
from agents.target_resolve import issue_target_delivery, resolve_target_step1
from models.state import EntityQuery
from network.delivery import get_delivery_store, reset_delivery_store
from network.paths import NetworkPaths, _RUNTIME_ENV_FIELDS
from network_helpers import import_seed_for_test

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_MANIFEST = REPO_ROOT / "examples" / "networks" / "baseball" / "network.json"
CRM_MANIFEST = REPO_ROOT / "examples" / "networks" / "crm" / "network.json"
CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm" / "seed.json"


def _apply_paths_monkeypatch(
    paths: NetworkPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(paths.root))
    for env_var, field in _RUNTIME_ENV_FIELDS.items():
        monkeypatch.setenv(env_var, str(getattr(paths, field)))


def _prepare_baseball_multi_grain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> NetworkPaths:
    root = tmp_path / "baseball"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    shutil.copy(REPO_ROOT / "examples" / "networks" / "baseball" / "guide.md", root / "guide.md")
    paths = NetworkPaths.from_root(root)
    _apply_paths_monkeypatch(paths, monkeypatch)
    reset_entity_registry()
    reset_delivery_store()

    team = get_entity_registry(grain="team")
    for entity_id, name in (
        ("team-brooklyn", "Brooklyn Dodgers"),
        ("team-la", "Los Angeles Dodgers"),
        ("team-yankees", "New York Yankees"),
    ):
        row = RegistryEntity(
            id=entity_id,
            bind_values={"name": name},
            source="test",
            created_at="2026-06-17T12:00:00+00:00",
        )
        team.register_entity(row)
        team.assign_bind_index(entity_id, row.bind_values)
        team.save_entity(row)

    player = get_entity_registry(grain="player")
    player_row = RegistryEntity(
        id="player-wash",
        bind_values={"name": "Washington", "team": "Washington Nationals"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    player.register_entity(player_row)
    player.assign_bind_index("player-wash", player_row.bind_values)
    player.save_entity(player_row)
    return paths


def _mock_disambiguation_chosen_team(
    hits,
    guide_text,
) -> GrainDisambiguationResult:
    _ = guide_text
    grains = {grain for grain, _, _ in hits}
    if grains == {"team", "player"}:
        return GrainDisambiguationResult(kind="chosen_grain", grain="team")
    return GrainDisambiguationResult(kind="ambiguous")


def _mock_disambiguation_ambiguous(
    hits,
    guide_text,
) -> GrainDisambiguationResult:
    _ = hits, guide_text
    return GrainDisambiguationResult(kind="ambiguous")


@pytest.mark.smoke
def test_filter_lookup_name_and_team_splits_grains() -> None:
    lookup = {"name": "Ada", "team": "Acme"}
    team_filtered = filter_lookup_for_grain(lookup, ["name"])
    player_filtered = filter_lookup_for_grain(lookup, ["name", "team"])
    assert team_filtered == {"name": "Ada"}
    assert player_filtered == {"name": "Ada", "team": "Acme"}


@pytest.mark.smoke
def test_team_only_lookup_skips_team_grain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_multi_grain(tmp_path, monkeypatch)
    lookup = {"team": "Washington Nationals"}
    participated = grains_with_filtered_lookup(lookup)
    assert "team" not in participated
    assert "player" in participated
    hits = fan_out_lookup(lookup)
    assert hits.get("team") is None
    assert hits.get("player") == ["player-wash"]


@pytest.mark.smoke
def test_fan_out_name_and_team_filters_team_grain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_multi_grain(tmp_path, monkeypatch)
    lookup = {"name": "Washington", "team": "Washington Nationals"}
    hits = fan_out_lookup(lookup)
    assert "team" not in hits
    assert hits.get("player") == ["player-wash"]


@pytest.mark.smoke
def test_mock_disambiguation_chosen_grain_team_multi_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_multi_grain(tmp_path, monkeypatch)
    team = get_entity_registry(grain="team")
    washington_team = RegistryEntity(
        id="team-wash",
        bind_values={"name": "Washington"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    team.register_entity(washington_team)
    team.assign_bind_index("team-wash", washington_team.bind_values)
    team.save_entity(washington_team)

    result = resolve_lookup_multi_grain(
        EntityQuery(lookup={"name": "Washington"}),
        disambiguator=_mock_disambiguation_chosen_team,
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["team-wash"]
    assert result.grain == "team"


@pytest.mark.smoke
def test_mock_disambiguation_ambiguous_lookup_suggested_with_grain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_multi_grain(tmp_path, monkeypatch)
    team = get_entity_registry(grain="team")
    washington_team = RegistryEntity(
        id="team-wash",
        bind_values={"name": "Washington"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    team.register_entity(washington_team)
    team.assign_bind_index("team-wash", washington_team.bind_values)
    team.save_entity(washington_team)

    result = resolve_lookup_multi_grain(
        EntityQuery(lookup={"name": "Washington"}),
        disambiguator=_mock_disambiguation_ambiguous,
    )
    assert result.kind == "lookup_suggested"
    grains = {item.grain for item in result.suggestions}
    assert grains == {"team", "player"}
    assert all(item.id for item in result.suggestions)


@pytest.mark.smoke
def test_resolve_id_sets_delivery_grain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_multi_grain(tmp_path, monkeypatch)
    result = resolve_id_all_grains("team-yankees")
    assert result.kind == "resolved"
    assert result.grain == "team"

    delivery = issue_target_delivery(
        EntityQuery(id="team-yankees"),
        result.entity_ids,
        grain=result.grain,
    )
    scope = get_delivery_store().get(delivery.delivery_id)
    assert scope is not None
    assert scope.grain == "team"
    loaded = load_delivery_scope(delivery.delivery_id)
    assert loaded.kind == "loaded"
    assert loaded.matched_records is not None
    assert loaded.matched_records[0]["id"] == "team-yankees"


@pytest.mark.smoke
def test_entity_query_grain_skips_fan_out(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_multi_grain(tmp_path, monkeypatch)
    result = resolve_target_step1(
        EntityQuery(lookup={"name": "New York Yankees"}, grain="team"),
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["team-yankees"]
    assert result.grain == "team"


@pytest.mark.smoke
def test_crm_single_grain_create_pending_still_works(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shutil.copy(CRM_MANIFEST, tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    import_seed_for_test(
        seed_src=CRM_SEED,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
    )
    reset_entity_registry()
    result = resolve_target_step1(
        EntityQuery(lookup={"name": "Road Runner", "employer": "Acme Corp"}),
    )
    assert result.kind == "create_pending"
    assert result.create_on_deliver is True

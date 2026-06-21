"""Smoke tests for strict lookup-key record type inference (no fan-out override)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.entity_registry import RegistryEntity, get_entity_registry, reset_entity_registry
from agents.target_deliver import load_delivery_scope
from agents.target_resolve import (
    issue_target_delivery,
    resolve_id_all_record_types,
    resolve_target_step1,
)
from models.state import EntityQuery
from network.delivery import get_delivery_store, reset_delivery_store
from network.paths import NetworkPaths
from network_helpers import apply_network_paths_monkeypatch, clear_network_path_env, import_seed_for_test

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_MANIFEST = REPO_ROOT / "examples" / "networks" / "baseball" / "network.json"
CRM_MANIFEST = REPO_ROOT / "examples" / "networks" / "crm-seeded" / "network.json"
CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm-seeded" / "seed.json"


def _prepare_baseball_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> NetworkPaths:
    root = tmp_path / "baseball"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    shutil.copy(REPO_ROOT / "examples" / "networks" / "baseball" / "guide.md", root / "guide.md")
    paths = NetworkPaths.from_root(root)
    clear_network_path_env(monkeypatch)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reset_entity_registry()
    reset_delivery_store()

    team = get_entity_registry(record_type="team")
    for entity_id, team_name in (
        ("team-brooklyn", "Brooklyn Dodgers"),
        ("team-la", "Los Angeles Dodgers"),
        ("team-yankees", "New York Yankees"),
    ):
        row = RegistryEntity(
            id=entity_id,
            bind_values={"team": team_name},
            source="test",
            created_at="2026-06-17T12:00:00+00:00",
        )
        team.register_entity(row)
        team.assign_bind_index(entity_id, row.bind_values)
        team.save_entity(row)

    player = get_entity_registry(record_type="player")
    player_row = RegistryEntity(
        id="player-wash",
        bind_values={
            "player": "Washington",
            "debut_team": "Washington Nationals",
            "debut_year": "2005",
        },
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    player.register_entity(player_row)
    player.assign_bind_index("player-wash", player_row.bind_values)
    player.save_entity(player_row)
    return paths


def _mock_team_alias_expander(
    record_type: str,
    field: str,
    query_value: str,
    registry,
    guide_text: str | None,
) -> list[str]:
    _ = record_type, field, registry, guide_text
    if query_value == "Bronx Bombers":
        return ["New York Yankees"]
    if query_value == "Dodgers":
        return ["Brooklyn Dodgers", "Los Angeles Dodgers"]
    if query_value == "The Miracle Mets":
        return ["New York Mets"]
    return []


@pytest.mark.smoke
def test_team_canonical_lookup_resolves_team_record_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    result = resolve_target_step1(EntityQuery(lookup={"team": "New York Yankees"}))
    assert result.kind == "resolved"
    assert result.entity_ids == ["team-yankees"]
    assert result.record_type == "team"


@pytest.mark.smoke
def test_team_nickname_resolves_via_mock_expander(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    result = resolve_target_step1(
        EntityQuery(lookup={"team": "Bronx Bombers"}),
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["team-yankees"]
    assert result.record_type == "team"


@pytest.mark.smoke
def test_team_dodgers_multi_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    team = get_entity_registry(record_type="team")
    team.add_field_alias("team-brooklyn", "team", "Dodgers")
    team.add_field_alias("team-la", "team", "Dodgers")

    result = resolve_target_step1(EntityQuery(lookup={"team": "Dodgers"}))
    assert result.kind == "resolved"
    assert set(result.entity_ids) == {"team-brooklyn", "team-la"}
    assert result.record_type == "team"


@pytest.mark.smoke
def test_player_full_mvr_routes_player_record_type_not_team(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    result = resolve_target_step1(
        EntityQuery(
            lookup={
                "player": "Washington",
                "debut_team": "Washington Nationals",
                "debut_year": "2005",
            },
        ),
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["player-wash"]
    assert result.record_type == "player"


@pytest.mark.smoke
def test_player_alias_bind_lookup_resolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    player = get_entity_registry(record_type="player")
    player_row = RegistryEntity(
        id="player-aaron",
        bind_values={
            "player": "Hank Aaron",
            "debut_team": "Brooklyn Dodgers",
            "debut_year": "1957",
        },
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    player.register_entity(player_row)
    player.assign_bind_index(player_row.id, player_row.bind_values)
    player.save_entity(player_row)
    player.add_bind_alias(
        player_row.id,
        {
            "player": "Hank Aaron",
            "debut_team": "Los Angeles Dodgers",
            "debut_year": "1958",
        },
    )

    result = resolve_target_step1(
        EntityQuery(
            lookup={
                "player": "Hank Aaron",
                "debut_team": "Los Angeles Dodgers",
                "debut_year": "1958",
            },
        ),
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["player-aaron"]
    assert result.record_type == "player"


def _no_op_alias_expander(
    record_type: str,
    field: str,
    query_value: str,
    registry,
    guide_text: str | None,
) -> list[str]:
    _ = record_type, field, query_value, registry, guide_text
    return []


@pytest.mark.smoke
def test_player_only_lookup_not_found_when_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    result = resolve_target_step1(
        EntityQuery(lookup={"player": "Nobody Here"}),
        alias_expander=_no_op_alias_expander,
    )
    assert result.kind == "not_found"


@pytest.mark.smoke
def test_player_only_lookup_resolved_unique(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    result = resolve_target_step1(EntityQuery(lookup={"player": "Washington"}))
    assert result.kind == "resolved"
    assert result.entity_ids == ["player-wash"]
    assert result.record_type == "player"


@pytest.mark.smoke
def test_player_only_homonym_multi_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    player = get_entity_registry(record_type="player")
    second = RegistryEntity(
        id="player-smith-2",
        bind_values={
            "player": "John Smith",
            "debut_team": "Boston Red Sox",
            "debut_year": "2010",
        },
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    first = RegistryEntity(
        id="player-smith-1",
        bind_values={
            "player": "John Smith",
            "debut_team": "Chicago Cubs",
            "debut_year": "2008",
        },
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    for row in (first, second):
        player.register_entity(row)
        player.assign_bind_index(row.id, row.bind_values)
        player.save_entity(row)

    result = resolve_target_step1(EntityQuery(lookup={"player": "John Smith"}))
    assert result.kind == "resolved"
    assert set(result.entity_ids) == {"player-smith-1", "player-smith-2"}
    assert result.record_type == "player"


@pytest.mark.smoke
def test_hank_aaron_milwaukee_resolves_one_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    player = get_entity_registry(record_type="player")
    player_row = RegistryEntity(
        id="player-aaron",
        bind_values={
            "player": "Hank Aaron",
            "debut_team": "Brooklyn Dodgers",
            "debut_year": "1957",
        },
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    player.register_entity(player_row)
    player.assign_bind_index(player_row.id, player_row.bind_values)
    player.save_entity(player_row)
    player.add_bind_alias(
        player_row.id,
        {
            "player": "Hank Aaron",
            "debut_team": "Milwaukee Braves",
            "debut_year": "1954",
        },
    )

    result = resolve_target_step1(
        EntityQuery(
            lookup={
                "player": "Hank Aaron",
                "debut_team": "Milwaukee Braves",
                "debut_year": "1954",
            },
        ),
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["player-aaron"]
    assert result.record_type == "player"


@pytest.mark.smoke
def test_duplicate_id_across_record_types_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    team = get_entity_registry(record_type="team")
    dup_team = RegistryEntity(
        id="dup-id",
        bind_values={"team": "Dup Team"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    team.register_entity(dup_team)
    team.assign_bind_index("dup-id", dup_team.bind_values)
    team.save_entity(dup_team)

    player = get_entity_registry(record_type="player")
    dup_player = RegistryEntity(
        id="dup-id",
        bind_values={
            "player": "Dup Player",
            "debut_team": "Dup City",
            "debut_year": "1999",
        },
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    player.register_entity(dup_player)
    player.assign_bind_index("dup-id", dup_player.bind_values)
    player.save_entity(dup_player)

    result = resolve_id_all_record_types("dup-id")
    assert result.kind == "not_found"


@pytest.mark.smoke
def test_resolve_id_sets_delivery_record_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_baseball_registry(tmp_path, monkeypatch)
    result = resolve_id_all_record_types("team-yankees")
    assert result.kind == "resolved"
    assert result.record_type == "team"

    delivery = issue_target_delivery(
        EntityQuery(id="team-yankees"),
        result.entity_ids,
        record_type=result.record_type,
    )
    scope = get_delivery_store().get(delivery.delivery_id)
    assert scope is not None
    assert scope.record_type == "team"
    loaded = load_delivery_scope(delivery.delivery_id)
    assert loaded.kind == "loaded"
    assert loaded.matched_records is not None
    assert loaded.matched_records[0]["id"] == "team-yankees"


@pytest.mark.smoke
def test_crm_single_record_type_create_pending_still_works(
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

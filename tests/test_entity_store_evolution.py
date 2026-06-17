"""Tests for EntityStore, deferred bootstrap save, and entity minisql_v1."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.entity_registry import (
    bootstrap_deferred_save,
    EntityRegistry,
    RegistryEntity,
    get_entity_registry,
    reset_entity_registry,
)
from network.mvr import load_mvr

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_MANIFEST = REPO_ROOT / "examples" / "networks" / "baseball" / "network.json"
CRM_MANIFEST = REPO_ROOT / "examples" / "networks" / "crm" / "network.json"
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"


def _copy_manifest(tmp_path: Path, manifest: Path) -> None:
    import shutil

    shutil.copy(manifest, tmp_path / "network.json")


def _person_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> EntityRegistry:
    import shutil

    _copy_manifest(tmp_path, CRM_MANIFEST)
    shutil.copy(SAMPLE_CATEGORIES, tmp_path / "categories.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities" / "person.json"))
    reset_entity_registry()
    return get_entity_registry(grain="person")


def _baseball_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    grain: str,
) -> EntityRegistry:
    _copy_manifest(tmp_path, BASEBALL_MANIFEST)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.delenv("MYCELIUM_ENTITIES_PATH", raising=False)
    reset_entity_registry()
    return get_entity_registry(grain=grain)


def _make_entity(entity_id: str, name: str, employer: str) -> RegistryEntity:
    return RegistryEntity(
        id=entity_id,
        bind_values={"name": name, "employer": employer},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )


@pytest.mark.smoke
def test_bootstrap_deferred_save_single_flush(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reg = _person_registry(tmp_path, monkeypatch)
    with patch.object(reg._store, "save", autospec=True) as save_mock:
        with bootstrap_deferred_save():
            for index in range(5):
                entity = _make_entity(f"id-{index}", f"Person {index}", "Acme Corp")
                reg.register_entity(entity)
                reg.assign_bind_index(entity.id, entity.bind_values)
                reg.save_entity(entity)
        assert save_mock.call_count == 1


@pytest.mark.smoke
def test_save_entity_without_deferred_flushes_each_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reg = _person_registry(tmp_path, monkeypatch)
    with patch.object(reg._store, "save", autospec=True) as save_mock:
        for index in range(3):
            entity = _make_entity(f"flush-{index}", f"Flush {index}", "Acme Corp")
            reg.register_entity(entity)
            reg.assign_bind_index(entity.id, entity.bind_values)
            reg.save_entity(entity)
    assert save_mock.call_count == 3


@pytest.mark.smoke
def test_entity_minisql_v1_json_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_ENTITY_OPTIMIZE_STORAGE_THRESHOLD", "2")
    reg = _baseball_registry(tmp_path, monkeypatch, "player")
    first = RegistryEntity(
        id="player-1",
        bind_values={"name": "Mike Trout", "team": "Angels"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    reg.register_entity(first)
    reg.assign_bind_index(first.id, first.bind_values)
    reg.save_entity(first)
    assert reg.path.is_file()

    second = RegistryEntity(
        id="player-2",
        bind_values={"name": "Shohei Ohtani", "team": "Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    reg.register_entity(second)
    reg.assign_bind_index(second.id, second.bind_values)
    reg.save_entity(second)

    json_path = reg.path
    assert reg._store.current_strategy() == "minisql_v1"
    assert not json_path.is_file()
    assert (json_path.parent / "player.json.pre-minisql-v1").is_file()
    assert reg._store.sqlite_path.is_file()
    strategy = json.loads(reg._store.strategy_path.read_text(encoding="utf-8"))
    assert strategy["last_migrated"] is not None


@pytest.mark.smoke
def test_entity_minisql_v1_migration_lookup_and_bind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_ENTITY_OPTIMIZE_STORAGE_THRESHOLD", "1")
    reg = _baseball_registry(tmp_path, monkeypatch, "team")
    entity = RegistryEntity(
        id="team-1",
        bind_values={"name": "New York Yankees"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    reg.register_entity(entity)
    reg.assign_bind_index(entity.id, entity.bind_values)
    reg.save_entity(entity)

    assert reg._store.current_strategy() == "minisql_v1"
    found = reg.lookup_by_bind_values({"name": "New York Yankees"})
    assert found is not None
    assert found.id == "team-1"
    assert reg._data.bind_index

    reg.reload()
    assert reg.lookup_by_id("team-1") is not None


@pytest.mark.smoke
def test_optimize_storage_skips_when_already_minisql(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_manifest(tmp_path, BASEBALL_MANIFEST)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    entities_dir = tmp_path / "entities"
    entities_dir.mkdir(parents=True)
    json_path = entities_dir / "player.json"
    strategy_path = entities_dir / "player.storage_strategy.json"
    strategy_path.write_text(
        json.dumps({"strategy": "minisql_v1", "last_migrated": "2026-06-17T00:00:00+00:00"}),
        encoding="utf-8",
    )
    mvr = load_mvr(grain="player")
    reg = EntityRegistry(path=json_path, grain="player", mvr=mvr)
    with patch.object(reg, "entity_count") as count_mock:
        assert reg.optimize_storage() is False
        count_mock.assert_not_called()


@pytest.mark.smoke
def test_add_bind_alias_skips_field_index_rebuild(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reg = _baseball_registry(tmp_path, monkeypatch, "player")
    entity = RegistryEntity(
        id="player-alias",
        bind_values={"name": "Hank Aaron", "team": "Brooklyn Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    reg.register_entity(entity)
    reg.assign_bind_index(entity.id, entity.bind_values)
    reg.save_entity(entity)

    with patch.object(reg, "_rebuild_field_indexes", autospec=True) as rebuild_mock:
        reg.add_bind_alias(
            entity.id,
            {"name": "Hank Aaron", "team": "Los Angeles Dodgers"},
        )

    rebuild_mock.assert_not_called()
    alias_hit = reg.lookup_by_bind_values(
        {"name": "Hank Aaron", "team": "Los Angeles Dodgers"},
    )
    assert alias_hit is not None
    assert alias_hit.id == entity.id


@pytest.mark.smoke
def test_save_entity_rebuilds_field_indexes_for_lookup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reg = _baseball_registry(tmp_path, monkeypatch, "player")
    entity = RegistryEntity(
        id="player-new",
        bind_values={"name": "Babe Ruth", "team": "New York Yankees"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )

    with patch.object(
        reg,
        "_rebuild_field_indexes",
        wraps=reg._rebuild_field_indexes,
    ) as rebuild_mock:
        reg.register_entity(entity)
        reg.assign_bind_index(entity.id, entity.bind_values)
        reg.save_entity(entity)

    rebuild_mock.assert_called_once()
    matches = reg.lookup_by_field("name", "Babe Ruth")
    assert len(matches) == 1
    assert matches[0].id == "player-new"


@pytest.mark.smoke
def test_lookup_by_source_key_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reg = _baseball_registry(tmp_path, monkeypatch, "player")
    entity = RegistryEntity(
        id="player-src",
        bind_values={"name": "Hank Aaron", "team": "Milwaukee Braves"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    reg.register_entity(entity)
    reg.assign_bind_index(entity.id, entity.bind_values)
    reg.set_source_keys(entity.id, {"lahman.playerID": "aaronha01"})
    assert reg.lookup_by_source_key("lahman.playerID", "aaronha01") is not None
    assert reg.lookup_by_source_key("lahman.playerID", "aaronha01").id == "player-src"

    reg.reload()
    assert reg.lookup_by_source_key("lahman.playerID", "aaronha01").id == "player-src"
    payload = json.loads(reg.path.read_text(encoding="utf-8"))
    assert payload["source_key_index"]["lahman.playerID|aaronha01"] == "player-src"


@pytest.mark.smoke
def test_add_field_alias_allows_multi_entity_lookup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reg = _baseball_registry(tmp_path, monkeypatch, "team")
    brooklyn = RegistryEntity(
        id="team-brooklyn",
        bind_values={"name": "Brooklyn Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    los_angeles = RegistryEntity(
        id="team-la",
        bind_values={"name": "Los Angeles Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    reg.register_entity(brooklyn)
    reg.assign_bind_index(brooklyn.id, brooklyn.bind_values)
    reg.save_entity(brooklyn)
    reg.register_entity(los_angeles)
    reg.assign_bind_index(los_angeles.id, los_angeles.bind_values)
    reg.save_entity(los_angeles)
    reg.add_field_alias(brooklyn.id, "name", "Dodgers")
    reg.add_field_alias(los_angeles.id, "name", "Dodgers")

    matched_ids = reg.lookup_by_target_lookup({"name": "Dodgers"})
    assert sorted(matched_ids) == ["team-brooklyn", "team-la"]

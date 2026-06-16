"""Unit tests for multi-grain MVR config and per-grain entity stores."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.entity_registry import RegistryEntity, get_entity_registry, reset_entity_registry
from network.bootstrap import run_network_bootstrap
from network.metering_policy import load_metering_policy
from network.mvr import (
    default_mvr_grain,
    list_mvr_grains,
    load_mvr,
    load_mvr_config,
)
from network.paths import NetworkPaths, _provisional_paths, apply_network_paths, entity_store_path

REPO_ROOT = Path(__file__).resolve().parent.parent
CRM_MANIFEST = REPO_ROOT / "examples" / "networks" / "crm" / "network.json"
BASEBALL_MANIFEST = REPO_ROOT / "examples" / "networks" / "baseball" / "network.json"
CRM_METERING = json.loads(CRM_MANIFEST.read_text(encoding="utf-8"))["metering"]


def _write_manifest(root: Path, manifest: dict) -> None:
    (root / "network.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def _minimal_person_manifest(**overrides: object) -> dict:
    manifest = {
        "name": "test-net",
        "mvr": {
            "default_grain": "person",
            "grains": {
                "person": {
                    "bind_fields": ["name", "employer"],
                    "description": "CRM people",
                },
            },
        },
        "metering": dict(CRM_METERING),
    }
    manifest.update(overrides)
    return manifest


@pytest.mark.smoke
def test_flat_bind_fields_rejected(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        {
            "name": "legacy",
            "mvr": {
                "bind_fields": ["name", "employer"],
                "description": "Legacy flat policy",
            },
            "metering": dict(CRM_METERING),
        },
    )
    paths = _provisional_paths(tmp_path.resolve())
    with pytest.raises(ValueError, match="flat mvr.bind_fields is not supported"):
        load_mvr_config(paths=paths)


@pytest.mark.smoke
def test_explicit_crm_grains_parse(tmp_path: Path) -> None:
    shutil.copy(CRM_MANIFEST, tmp_path / "network.json")
    paths = NetworkPaths.from_root(tmp_path)
    config = load_mvr_config(paths=paths)
    assert config.default_grain == "person"
    assert list_mvr_grains(paths=paths) == ["person"]
    assert entity_store_path(paths, "person") == tmp_path / "entities" / "person.json"
    assert paths.entities_path == tmp_path / "entities" / "person.json"


@pytest.mark.smoke
def test_missing_network_json_raises(tmp_path: Path) -> None:
    paths = _provisional_paths(tmp_path.resolve())
    with pytest.raises(ValueError, match="network manifest required"):
        load_mvr_config(paths=paths)


@pytest.mark.smoke
def test_missing_mvr_raises(tmp_path: Path) -> None:
    _write_manifest(tmp_path, {"name": "no-mvr", "metering": dict(CRM_METERING)})
    paths = _provisional_paths(tmp_path.resolve())
    with pytest.raises(ValueError, match="missing required mvr object"):
        load_mvr_config(paths=paths)


@pytest.mark.smoke
def test_missing_metering_raises(tmp_path: Path) -> None:
    manifest = _minimal_person_manifest()
    manifest.pop("metering")
    _write_manifest(tmp_path, manifest)
    paths = NetworkPaths.from_root(tmp_path)
    with pytest.raises(ValueError, match="missing required metering object"):
        load_metering_policy(paths=paths)


@pytest.mark.smoke
def test_single_grain_requires_default_grain(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        {
            "name": "one-grain",
            "mvr": {
                "grains": {
                    "person": {
                        "bind_fields": ["name", "employer"],
                        "description": "person only",
                    },
                },
            },
            "metering": dict(CRM_METERING),
        },
    )
    paths = _provisional_paths(tmp_path.resolve())
    with pytest.raises(ValueError, match="missing required mvr.default_grain"):
        load_mvr_config(paths=paths)


@pytest.mark.smoke
def test_baseball_manifest_requires_default_grain_for_two_grains(
    tmp_path: Path,
) -> None:
    manifest = json.loads(BASEBALL_MANIFEST.read_text(encoding="utf-8"))
    manifest["mvr"].pop("default_grain")
    _write_manifest(tmp_path, manifest)
    paths = _provisional_paths(tmp_path.resolve())
    with pytest.raises(ValueError, match="missing required mvr.default_grain"):
        load_mvr_config(paths=paths)


@pytest.mark.smoke
def test_baseball_manifest_parses_two_grains(tmp_path: Path) -> None:
    shutil.copy(BASEBALL_MANIFEST, tmp_path / "network.json")
    paths = NetworkPaths.from_root(tmp_path)
    config = load_mvr_config(paths=paths)
    assert config.default_grain == "player"
    assert list_mvr_grains(paths=paths) == ["player", "team"]
    assert load_mvr(paths=paths, grain="team").bind_fields == ["name"]


@pytest.mark.smoke
def test_unknown_grain_raises(tmp_path: Path) -> None:
    shutil.copy(CRM_MANIFEST, tmp_path / "network.json")
    paths = NetworkPaths.from_root(tmp_path)
    with pytest.raises(ValueError, match="Unknown MVR grain"):
        load_mvr(paths=paths, grain="team")


@pytest.mark.smoke
def test_entity_store_uses_grain_path_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shutil.copy(CRM_MANIFEST, tmp_path / "network.json")
    legacy_payload = json.dumps({"version": "1.0", "entities": {}, "bind_index": {}})
    (tmp_path / "entities.json").write_text(legacy_payload, encoding="utf-8")
    paths = NetworkPaths.from_root(tmp_path)
    grain_path = entity_store_path(paths, "person")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.delenv("MYCELIUM_ENTITIES_PATH", raising=False)
    reset_entity_registry()
    registry = get_entity_registry()
    assert registry.entity_count() == 0
    registry.bind_provisional("Grace Hopper", "Navy")
    assert grain_path.is_file()
    assert json.loads((tmp_path / "entities.json").read_text(encoding="utf-8"))["entities"] == {}


@pytest.mark.smoke
def test_per_grain_registry_isolation(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        {
            "name": "multi",
            "mvr": {
                "default_grain": "player",
                "grains": {
                    "player": {
                        "bind_fields": ["name", "team"],
                        "description": "player grain",
                    },
                    "team": {
                        "bind_fields": ["name"],
                        "description": "team grain",
                    },
                },
            },
            "metering": dict(CRM_METERING),
        },
    )
    paths = NetworkPaths.from_root(tmp_path)
    apply_network_paths(paths)
    reset_entity_registry()

    player = get_entity_registry(grain="player")
    team = get_entity_registry(grain="team")
    player_entity = RegistryEntity(
        id="player-1",
        bind_values={"name": "Babe Ruth", "team": "NYY"},
        validation_state="provisional",
        source="query_bind",
        created_at="2026-01-01T00:00:00+00:00",
    )
    player.register_entity(player_entity)
    player.assign_bind_index("player-1", {"name": "Babe Ruth", "team": "NYY"})
    player.save_entity(player_entity)
    team_entity = RegistryEntity(
        id="team-1",
        bind_values={"name": "New York Yankees"},
        validation_state="provisional",
        source="query_bind",
        created_at="2026-01-01T00:00:00+00:00",
    )
    team.register_entity(team_entity)
    team.assign_bind_index("team-1", {"name": "New York Yankees"})
    team.save_entity(team_entity)

    assert player.entity_count() == 1
    assert team.entity_count() == 1
    assert player.lookup_by_field("name", "New York Yankees") == []
    assert (tmp_path / "entities" / "player.json").is_file()
    assert (tmp_path / "entities" / "team.json").is_file()


@pytest.mark.smoke
def test_reset_entity_registry_clears_all_grains(tmp_path: Path) -> None:
    shutil.copy(BASEBALL_MANIFEST, tmp_path / "network.json")
    paths = NetworkPaths.from_root(tmp_path)
    apply_network_paths(paths)
    reset_entity_registry()
    get_entity_registry(grain="player")
    get_entity_registry(grain="team")
    reset_entity_registry()
    assert get_entity_registry(grain="player").entity_count() == 0
    assert get_entity_registry(grain="team").entity_count() == 0


@pytest.mark.smoke
def test_baseball_bootstrap_commits_zero_rows(tmp_path: Path) -> None:
    shutil.copy(BASEBALL_MANIFEST, tmp_path / "network.json")
    handlers_src = REPO_ROOT / "examples" / "networks" / "baseball" / "bootstrap_handlers"
    shutil.copytree(handlers_src, tmp_path / "bootstrap_handlers")
    paths = NetworkPaths.from_root(tmp_path)
    apply_network_paths(paths)
    result = run_network_bootstrap(paths)
    assert result.handler_id == "lahman_seed"
    assert result.entities_committed == 0
    assert get_entity_registry(grain="player").entity_count() == 0
    assert get_entity_registry(grain="team").entity_count() == 0
    assert default_mvr_grain(paths=paths) == "player"

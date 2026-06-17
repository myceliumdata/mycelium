"""Smoke tests for baseball LahmanSeedHandler pack bootstrap."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.entity_registry import get_entity_registry, reset_entity_registry
from network.bootstrap import run_network_bootstrap
from network.paths import NetworkPaths, apply_network_paths, entity_store_path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_EXAMPLE = REPO_ROOT / "examples" / "networks" / "baseball"
BASEBALL_MANIFEST = BASEBALL_EXAMPLE / "network.json"


def _write_minimal_lahman_fixture(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "Teams.csv").write_text(
        "yearID,lgID,teamID,franchID,name\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers\n"
        "1958,NL,LAN,LAD,Los Angeles Dodgers\n"
        "2024,NL,MIL,MIL,Milwaukee Brewers\n",
        encoding="utf-8",
    )
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast\n"
        "1,aaronha01,Hank,Aaron\n",
        encoding="utf-8",
    )
    (seed_dir / "Appearances.csv").write_text(
        "yearID,teamID,playerID\n"
        "1957,BRO,aaronha01\n",
        encoding="utf-8",
    )


def _write_multi_team_fixture(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "Teams.csv").write_text(
        "yearID,lgID,teamID,franchID,name\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers\n"
        "1958,NL,LAN,LAD,Los Angeles Dodgers\n",
        encoding="utf-8",
    )
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast\n"
        "1,aaronha01,Hank,Aaron\n",
        encoding="utf-8",
    )
    (seed_dir / "Appearances.csv").write_text(
        "yearID,teamID,playerID\n"
        "1957,BRO,aaronha01\n"
        "1958,LAN,aaronha01\n",
        encoding="utf-8",
    )


def _prepare_baseball_root(tmp_path: Path, *, seed_fixture: str | None) -> NetworkPaths:
    root = tmp_path / "baseball-live"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    shutil.copytree(BASEBALL_EXAMPLE / "bootstrap_handlers", root / "bootstrap_handlers")
    if seed_fixture == "minimal":
        _write_minimal_lahman_fixture(root / "seed")
    elif seed_fixture == "multi_team":
        _write_multi_team_fixture(root / "seed")
    return NetworkPaths.from_root(root)


@pytest.mark.smoke
def test_lahman_seed_handler_no_seed_commits_zero(tmp_path: Path) -> None:
    paths = _prepare_baseball_root(tmp_path, seed_fixture=None)
    apply_network_paths(paths)
    result = run_network_bootstrap(paths)
    assert result.handler_id == "lahman_seed"
    assert result.entities_committed == 0
    assert result.sources_processed == []


@pytest.mark.smoke
def test_lahman_seed_handler_commits_teams_and_players(tmp_path: Path) -> None:
    paths = _prepare_baseball_root(tmp_path, seed_fixture="minimal")
    apply_network_paths(paths)
    result = run_network_bootstrap(paths)
    assert result.handler_id == "lahman_seed"
    assert result.entities_committed == 4
    assert result.entities_by_grain == {"team": 3, "player": 1}

    team_path = entity_store_path(paths, "team")
    player_path = entity_store_path(paths, "player")
    team_names = {
        e["bind_values"]["name"]
        for e in json.loads(team_path.read_text(encoding="utf-8"))["entities"].values()
    }
    assert team_names == {
        "Brooklyn Dodgers",
        "Los Angeles Dodgers",
        "Milwaukee Brewers",
    }
    player_payload = json.loads(player_path.read_text(encoding="utf-8"))
    assert len(player_payload["entities"]) == 1
    player = next(iter(player_payload["entities"].values()))
    assert player["bind_values"]["name"] == "Hank Aaron"
    assert player["bind_values"]["team"] == "Brooklyn Dodgers"
    assert player["source_keys"]["lahman.playerID"] == "aaronha01"
    assert (paths.root / "warehouse" / "lahman.sqlite").is_file()


@pytest.mark.smoke
def test_lahman_seed_handler_multi_team_same_player_id(tmp_path: Path) -> None:
    paths = _prepare_baseball_root(tmp_path, seed_fixture="multi_team")
    apply_network_paths(paths)
    result = run_network_bootstrap(paths)
    assert result.handler_id == "lahman_seed"
    assert result.entities_by_grain == {"team": 2, "player": 1}

    reset_entity_registry()
    player_registry = get_entity_registry(grain="player")
    assert player_registry.entity_count() == 1

    brooklyn = player_registry.lookup_by_bind_values(
        {"name": "Hank Aaron", "team": "Brooklyn Dodgers"},
    )
    los_angeles = player_registry.lookup_by_bind_values(
        {"name": "Hank Aaron", "team": "Los Angeles Dodgers"},
    )
    assert brooklyn is not None
    assert los_angeles is not None
    assert brooklyn.id == los_angeles.id
    assert brooklyn.source_keys["lahman.playerID"] == "aaronha01"

    brooklyn_target = player_registry.lookup_by_target_lookup(
        {"name": "Hank Aaron", "team": "Brooklyn Dodgers"},
    )
    los_angeles_target = player_registry.lookup_by_target_lookup(
        {"name": "Hank Aaron", "team": "Los Angeles Dodgers"},
    )
    assert brooklyn_target == [brooklyn.id]
    assert los_angeles_target == [los_angeles.id]
    assert brooklyn_target == los_angeles_target

    player_path = entity_store_path(paths, "player")
    payload = json.loads(player_path.read_text(encoding="utf-8"))
    assert len(payload["bind_index"]) == 2
    entity_ids = set(payload["bind_index"].values())
    assert len(entity_ids) == 1

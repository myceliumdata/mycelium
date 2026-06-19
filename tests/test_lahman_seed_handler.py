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
        "ID,playerID,nameFirst,nameLast,debut\n"
        "1,aaronha01,Hank,Aaron,\n",
        encoding="utf-8",
    )
    (seed_dir / "Appearances.csv").write_text(
        "yearID,teamID,playerID\n"
        "1957,BRO,aaronha01\n",
        encoding="utf-8",
    )
    (seed_dir / "Batting.csv").write_text(
        "playerID,yearID,stint,teamID,lgID,G,AB,R,H,2B,3B,HR,RBI,SB,CS,BB,SO,IBB,HBP,SH,SF,GIDP\n"
        "aaronha01,1957,1,BRO,NL,1,4,0,2,0,0,1,1,0,0,0,0,0,0,0,0,0\n"
        "aaronha01,1958,1,LAN,NL,1,4,0,2,0,0,2,2,0,0,0,0,0,0,0,0,0\n",
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
        "ID,playerID,nameFirst,nameLast,debut\n"
        "1,aaronha01,Hank,Aaron,\n",
        encoding="utf-8",
    )
    (seed_dir / "Appearances.csv").write_text(
        "yearID,teamID,playerID\n"
        "1957,BRO,aaronha01\n"
        "1958,LAN,aaronha01\n",
        encoding="utf-8",
    )
    (seed_dir / "Batting.csv").write_text(
        "playerID,yearID,stint,teamID,lgID,G,AB,R,H,2B,3B,HR,RBI,SB,CS,BB,SO,IBB,HBP,SH,SF,GIDP\n"
        "aaronha01,1957,1,BRO,NL,1,4,0,2,0,0,1,1,0,0,0,0,0,0,0,0,0\n"
        "aaronha01,1958,1,LAN,NL,1,4,0,2,0,0,2,2,0,0,0,0,0,0,0,0,0\n",
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
    assert result.entities_by_record_type == {"team": 3, "player": 1}

    team_path = entity_store_path(paths, "team")
    player_path = entity_store_path(paths, "player")
    team_names = {
        e["bind_values"]["team"]
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
    assert player["bind_values"]["player"] == "Hank Aaron"
    assert player["bind_values"]["debut_team"] == "Brooklyn Dodgers"
    assert player["bind_values"]["debut_year"] == "1957"
    assert player["source_keys"]["lahman.playerID"] == "aaronha01"
    assert (paths.root / "warehouse" / "lahman.sqlite").is_file()


@pytest.mark.smoke
def test_lahman_seed_handler_multi_team_same_player_id(tmp_path: Path) -> None:
    paths = _prepare_baseball_root(tmp_path, seed_fixture="multi_team")
    apply_network_paths(paths)
    result = run_network_bootstrap(paths)
    assert result.handler_id == "lahman_seed"
    assert result.entities_by_record_type == {"team": 2, "player": 1}

    reset_entity_registry()
    player_registry = get_entity_registry(record_type="player")
    assert player_registry.entity_count() == 1

    player = player_registry.lookup_by_bind_values(
        {
            "player": "Hank Aaron",
            "debut_team": "Brooklyn Dodgers",
            "debut_year": "1957",
        },
    )
    assert player is not None
    assert player.source_keys["lahman.playerID"] == "aaronha01"

    la_lookup = player_registry.lookup_by_bind_values(
        {
            "player": "Hank Aaron",
            "debut_team": "Los Angeles Dodgers",
            "debut_year": "1958",
        },
    )
    assert la_lookup is None

    player_path = entity_store_path(paths, "player")
    payload = json.loads(player_path.read_text(encoding="utf-8"))
    assert len(payload["bind_index"]) == 1
    entity_ids = set(payload["bind_index"].values())
    assert len(entity_ids) == 1

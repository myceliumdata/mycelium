"""Smoke tests for baseball LahmanSeedHandler pack bootstrap."""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from agents.entity_registry import get_entity_registry, reset_entity_registry
from network.bootstrap import run_network_bootstrap
from network.paths import NetworkPaths, apply_network_paths, entity_store_path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_EXAMPLE = REPO_ROOT / "examples" / "networks" / "baseball"
BASEBALL_MANIFEST = BASEBALL_EXAMPLE / "network.json"

# One-row stubs for every Lahman 2025 table (see lahman_common.BOOTSTRAP_TABLES).
_FULL_LAHMAN_FIXTURE_CSV: dict[str, str] = {
    "Teams.csv": (
        "yearID,lgID,teamID,franchID,name\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers\n"
        "1958,NL,LAN,LAD,Los Angeles Dodgers\n"
        "2024,NL,MIL,MIL,Milwaukee Brewers\n"
    ),
    "People.csv": (
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut\n"
        "1,aaronha01,Hank,Aaron,1934,2,5,\n"
    ),
    "TeamsFranchises.csv": (
        "franchID,franchName,active,NAassoc\n"
        "LAD,Dodgers,Y,\n"
    ),
    "Parks.csv": (
        "ID,parkalias,parkkey,parkname,city,state,country\n"
        "1,Ebbets Field,E01,Ebbets Field,Brooklyn,NY,US\n"
    ),
    "Schools.csv": (
        "schoolID,name_full,city,state,country\n"
        "school1,Example High,Springfield,IL,US\n"
    ),
    "Appearances.csv": (
        "yearID,teamID,playerID\n"
        "1957,BRO,aaronha01\n"
    ),
    "Batting.csv": (
        "playerID,yearID,stint,teamID,lgID,G,AB,R,H,2B,3B,HR,RBI,SB,CS,BB,SO,IBB,HBP,SH,SF,GIDP\n"
        "aaronha01,1957,1,BRO,NL,1,4,0,2,0,0,1,1,0,0,0,0,0,0,0,0,0\n"
    ),
    "Pitching.csv": (
        "playerID,yearID,stint,teamID,lgID,W,L,G,GS,CG,SHO,SV,IPouts,H,ER,HR,BB,SO,BAOpp,ERA,IBB,WP,HBP,BK,GF,R,SH,SF,GIDP\n"
        "aaronha01,1957,1,BRO,NL,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n"
    ),
    "Fielding.csv": (
        "playerID,yearID,stint,teamID,lgID,Pos,G,GS,InnOuts,PO,A,E,DP,PB,WP,SB,CS,ZR\n"
        "aaronha01,1957,1,BRO,NL,RF,1,1,27,1,0,0,0,,,,,\n"
    ),
    "FieldingOF.csv": (
        "playerID,yearID,stint,Glf,Gcf,Grf\n"
        "aaronha01,1957,1,0,0,1\n"
    ),
    "FieldingOFsplit.csv": (
        "playerID,yearID,stint,teamID,lgID,POS,G,GS,InnOuts,PO,A,E,DP,PB,WP,SB,CS,ZR\n"
        "aaronha01,1957,1,BRO,NL,RF,1,1,27,1,0,0,0,,,,,\n"
    ),
    "Managers.csv": (
        "playerID,yearID,teamID,lgID,inseason,G,W,L,rank,plyrMgr\n"
        "aaronha01,1957,BRO,NL,1,1,1,0,1,N\n"
    ),
    "ManagersHalf.csv": (
        "playerID,yearID,teamID,lgID,inseason,half,G,W,L,rank\n"
        "aaronha01,1957,BRO,NL,1,1,1,1,0,1\n"
    ),
    "HomeGames.csv": (
        "yearkey,leaguekey,teamkey,parkkey,spanfirst,spanlast,games,openings,attendance\n"
        "1957,NL,BRO,E01,19570415,19570924,77,77,1000\n"
    ),
    "TeamsHalf.csv": (
        "yearID,lgID,teamID,Half,divID,DivWin,Rank,G,W,L\n"
        "1981,NL,BRO,1,E,N,1,1,1,0\n"
    ),
    "BattingPost.csv": (
        "yearID,round,playerID,teamID,lgID,G,AB,R,H,2B,3B,HR,RBI,SB,CS,BB,SO,IBB,HBP,SH,SF,GIDP\n"
        "1957,WS,aaronha01,BRO,NL,1,4,0,2,0,0,1,1,0,0,0,0,0,0,0,0,0\n"
    ),
    "PitchingPost.csv": (
        "playerID,yearID,round,teamID,lgID,W,L,G,GS,CG,SHO,SV,IPouts,H,ER,HR,BB,SO,BAOpp,ERA,IBB,WP,HBP,BK,BFP,GF,R,SH,SF,GIDP\n"
        "aaronha01,1957,WS,BRO,NL,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n"
    ),
    "FieldingPost.csv": (
        "playerID,yearID,teamID,lgID,round,POS,G,GS,InnOuts,PO,A,E,DP,TP,PB,SB,CS\n"
        "aaronha01,1957,BRO,NL,WS,RF,1,1,27,1,0,0,0,0,,,\n"
    ),
    "SeriesPost.csv": (
        "yearID,round,teamIDwinner,lgIDwinner,teamIDloser,lgIDloser,wins,losses,ties\n"
        "1957,WS,NYA,AL,BRO,NL,4,3,0\n"
    ),
    "AllstarFull.csv": (
        "playerID,yearID,gameNum,gameID,teamID,lgID,GP,startingPos\n"
        "aaronha01,1957,0,,BRO,NL,1,\n"
    ),
    "HallOfFame.csv": (
        "playerID,yearid,votedBy,ballots,needed,votes,inducted,category,needed_note\n"
        "aaronha01,1982,BBW,415,312,406,Y,Player,\n"
    ),
    "AwardsPlayers.csv": (
        "playerID,awardID,yearID,lgID,tie,notes\n"
        "aaronha01,MVP,1957,NL,,\n"
    ),
    "AwardsManagers.csv": (
        "playerID,awardID,yearID,lgID,tie,notes\n"
        "aaronha01,Mgr of the year,1957,NL,,\n"
    ),
    "AwardsSharePlayers.csv": (
        "awardID,yearID,lgID,playerID,pointsWon,pointsMax,votesFirst\n"
        "MVP,1957,NL,aaronha01,10,336,1\n"
    ),
    "AwardsShareManagers.csv": (
        "awardID,yearID,lgID,playerID,pointsWon,pointsMax,votesFirst\n"
        "Mgr of the year,1957,NL,aaronha01,1,120,0\n"
    ),
    "CollegePlaying.csv": (
        "playerID,schoolID,yearID\n"
        "aaronha01,school1,1952\n"
    ),
    "Salaries.csv": (
        "yearID,teamID,lgID,playerID,salary\n"
        "1957,BRO,NL,aaronha01,28000\n"
    ),
}


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
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut\n"
        "1,aaronha01,Hank,Aaron,1934,2,5,\n",
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


def _write_full_lahman_fixture(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    for name, body in _FULL_LAHMAN_FIXTURE_CSV.items():
        (seed_dir / name).write_text(body, encoding="utf-8")


def _write_multi_team_fixture(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "Teams.csv").write_text(
        "yearID,lgID,teamID,franchID,name\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers\n"
        "1958,NL,LAN,LAD,Los Angeles Dodgers\n",
        encoding="utf-8",
    )
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut\n"
        "1,aaronha01,Hank,Aaron,1934,2,5,\n",
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
    elif seed_fixture == "full":
        _write_full_lahman_fixture(root / "seed")
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


@pytest.mark.smoke
def test_lahman_seed_handler_ingests_all_lahman_tables(tmp_path: Path) -> None:
    paths = _prepare_baseball_root(tmp_path, seed_fixture="full")
    apply_network_paths(paths)
    result = run_network_bootstrap(paths)
    assert result.handler_id == "lahman_seed"
    assert len(result.warehouse_ingest_counts) == 27
    assert all(count > 0 for count in result.warehouse_ingest_counts.values())

    warehouse_path = paths.root / "warehouse" / "lahman.sqlite"
    conn = sqlite3.connect(warehouse_path)
    try:
        for table, expected_rows in result.warehouse_ingest_counts.items():
            safe = table.replace('"', '""')
            actual = conn.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0]
            assert actual == expected_rows
            assert actual > 0
    finally:
        conn.close()

    manifest_path = paths.root / "warehouse_manifest.json"
    assert manifest_path.is_file()

"""Shared minimal Lahman CSV fixture for baseball smoke tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.entity_registry import reset_entity_registry
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from graphs.core import reset_core_graph
from network.delivery import reset_delivery_store
from network.example import refresh_example_network
from network.paths import NetworkPaths
from network_helpers import apply_network_paths_monkeypatch
from storage.core import reset_storage

SAMPLE_PLAYER = {
    "player": "Hank Aaron",
    "debut_team": "Brooklyn Dodgers",
    "debut_year": "1957",
}


def write_minimal_lahman_fixture(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "Teams.csv").write_text(
        "yearID,lgID,teamID,franchID,name,W,L,Rank,park,R,RA\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers,84,70,3,Ebbets Field,800,750\n"
        "1958,NL,LAN,LAD,Los Angeles Dodgers,71,83,7,Dodger Stadium,600,700\n"
        "2024,NL,MIL,MIL,Milwaukee Brewers,92,70,1,American Family Field,750,720\n",
        encoding="utf-8",
    )
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut,"
        "height,weight,birthCountry,finalGame,deathYear,deathMonth,deathDay,bats,throws,birthCity\n"
        "1,aaronha01,Hank,Aaron,1934,2,5,,72,180,USA,1976-10-03,2021,1,22,R,R,Mobile\n",
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
    (seed_dir / "Pitching.csv").write_text(
        "playerID,yearID,stint,teamID,lgID,W,L,G,GS,CG,SHO,SV,IPouts,H,ER,HR,BB,SO,BAOpp,ERA,IBB,WP,HBP,BK,GF,R,SH,SF,GIDP\n"
        "aaronha01,1957,1,BRO,NL,2,1,5,0,0,0,0,27,0,3,0,0,0,3,0,0,0,0,0,0,0,0,0,0\n"
        "aaronha01,1958,1,LAN,NL,3,0,4,0,0,0,1,54,0,6,0,0,0,5,0,0,0,0,0,0,0,0,0,0\n",
        encoding="utf-8",
    )
    (seed_dir / "Fielding.csv").write_text(
        "playerID,yearID,stint,teamID,lgID,Pos,G,GS,InnOuts,PO,A,E,DP,PB,WP,SB,CS,ZR\n"
        "aaronha01,1957,1,BRO,NL,RF,10,10,270,20,5,0,0,,,,,\n"
        "aaronha01,1958,1,LAN,NL,RF,5,5,135,5,2,0,0,,,,,\n",
        encoding="utf-8",
    )


def reset_runtime() -> None:
    for reset_fn in (
        reset_storage,
        reset_entity_registry,
        reset_core_graph,
        reset_category_tree,
        reset_delivery_store,
        reset_agent_registry,
        reset_agent_factory,
    ):
        reset_fn(    )


def write_missing_birth_month_fixture(seed_dir: Path) -> None:
    write_minimal_lahman_fixture(seed_dir)
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut,"
        "height,weight,birthCountry,finalGame,deathYear,deathMonth,deathDay,bats,throws,birthCity\n"
        "1,aaronha01,Hank,Aaron,1934,,5,,72,180,USA,1976-10-03,2021,1,22,R,R,Mobile\n",
        encoding="utf-8",
    )


def write_missing_death_month_fixture(seed_dir: Path) -> None:
    write_minimal_lahman_fixture(seed_dir)
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut,"
        "height,weight,birthCountry,finalGame,deathYear,deathMonth,deathDay,bats,throws,birthCity\n"
        "1,aaronha01,Hank,Aaron,1934,2,5,,72,180,USA,1976-10-03,2021,,22,R,R,Mobile\n",
        encoding="utf-8",
    )


def write_zero_ipouts_pitching_fixture(seed_dir: Path) -> None:
    write_minimal_lahman_fixture(seed_dir)
    (seed_dir / "Pitching.csv").write_text(
        "playerID,yearID,stint,teamID,lgID,W,L,G,GS,CG,SHO,SV,IPouts,H,ER,HR,BB,SO,BAOpp,ERA,IBB,WP,HBP,BK,GF,R,SH,SF,GIDP\n"
        "aaronha01,1957,1,BRO,NL,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n",
        encoding="utf-8",
    )


def refresh_baseball_root_with_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    fixture_fn=write_minimal_lahman_fixture,
) -> Path:
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fixture_csv = tmp_path / "lahman-fixture" / "lahman_1871-2025_csv"
    fixture_fn(fixture_csv)
    root = tmp_path / "baseball-live"

    def fake_fetch(network_root: Path, *, progress=None) -> str:
        dest = network_root / "seed" / "lahman_1871-2025_csv"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(fixture_csv, dest)
        return "lahman-seed@v2025.1-minimal-smoke"

    monkeypatch.setattr("network.example.fetch_example_seed", fake_fetch)
    refresh_example_network("baseball", root=root, register=False, yes=True)
    paths = NetworkPaths.from_root(root)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    reset_runtime()
    reset_core_graph()
    return root


def refresh_baseball_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    return refresh_baseball_root_with_fixture(tmp_path, monkeypatch)
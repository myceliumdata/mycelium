"""Multi-attribute deliver: registry bind + warehouse specialists + provenance."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.entity_registry import reset_entity_registry
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
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


def _write_minimal_lahman_fixture(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "Teams.csv").write_text(
        "yearID,lgID,teamID,franchID,name\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers\n",
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


def _reset_runtime() -> None:
    for reset_fn in (
        reset_storage,
        reset_entity_registry,
        reset_core_graph,
        reset_category_tree,
        reset_delivery_store,
        reset_agent_registry,
        reset_agent_factory,
    ):
        reset_fn()


def _refresh_baseball_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fixture_csv = tmp_path / "lahman-fixture" / "lahman_1871-2025_csv"
    _write_minimal_lahman_fixture(fixture_csv)
    root = tmp_path / "baseball-live"

    def fake_fetch(network_root: Path, *, progress=None) -> str:
        dest = network_root / "seed" / "lahman_1871-2025_csv"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(fixture_csv, dest)
        return "lahman-seed@v2025.1"

    monkeypatch.setattr("network.example.fetch_example_seed", fake_fetch)
    refresh_example_network("baseball", root=root, register=False, yes=True)
    paths = NetworkPaths.from_root(root)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    _reset_runtime()
    reset_core_graph()
    return root


@pytest.mark.smoke
def test_multi_attr_bind_and_warehouse_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _refresh_baseball_root(tmp_path, monkeypatch)
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=["debut_team", "career_hr", "birth_date"],
        provenance=True,
    )
    r1 = run_query(step1, thread_id="multi-attr-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="multi-attr-step2",
    )
    assert r2.outcome in {"found", "assembled"}
    assert r2.provenance is not None
    attrs = r2.provenance["entities"][0]["attributes"]

    bind_version = attrs["debut_team"]["versions"][0]
    assert bind_version["actor"]["kind"] in {"registry", "seed_bootstrap"}
    assert bind_version["actor"]["kind"] != "research"

    hr_version = attrs["career_hr"]["versions"][0]
    assert hr_version["parameters"]["warehouse"] == "warehouse/lahman.sqlite"
    assert hr_version["parameters"]["attribute"] == "career_hr"
    assert hr_version["parameters"]["column"] == "HR"

    bio_version = attrs["birth_date"]["versions"][0]
    assert bio_version["parameters"]["warehouse"] == "warehouse/lahman.sqlite"
    assert bio_version["parameters"]["attribute"] == "birth_date"

    row = r2.results[0]
    assert row.get("debut_team") == "Brooklyn Dodgers"
    assert str(row.get("career_hr")) == "3"
    assert row.get("birth_date") == "1934-02-05"

"""Smoke tests for baseball bio specialist raw warehouse read + provenance."""

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
from baseball_minimal_fixture import refresh_baseball_root as refresh_shared_fixture

SAMPLE_PLAYER = {
    "player": "Hank Aaron",
    "debut_team": "Brooklyn Dodgers",
    "debut_year": "1957",
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


def _write_missing_birth_month_fixture(seed_dir: Path) -> None:
    _write_minimal_lahman_fixture(seed_dir)
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut\n"
        "1,aaronha01,Hank,Aaron,1934,,5,\n",
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


def _refresh_baseball_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    fixture_fn=_write_minimal_lahman_fixture,
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
        return "lahman-seed@v2025.1"

    monkeypatch.setattr("network.example.fetch_example_seed", fake_fetch)
    refresh_example_network("baseball", root=root, register=False, yes=True)
    paths = NetworkPaths.from_root(root)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    _reset_runtime()
    reset_core_graph()
    return root


def _deliver_birth_date(*, provenance: bool = False) -> tuple[object, object]:
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=["birth_date"],
        provenance=provenance,
    )
    r1 = run_query(step1, thread_id="birth-date-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    step2 = EntityQuery(delivery_id=r1.delivery.delivery_id)
    r2 = run_query(step2, thread_id="birth-date-step2")
    return r1, r2


@pytest.mark.smoke
def test_birth_date_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_birth_date()
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert response.results[0].get("birth_date") == "1934-02-05"


@pytest.mark.smoke
def test_birth_date_provenance_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_birth_date(provenance=True)
    assert response.provenance is not None
    attrs = response.provenance["entities"][0]["attributes"]
    version = attrs["birth_date"]["versions"][0]
    assert version["status"] == "found"
    assert version["value"] == "1934-02-05"
    assert version["sources"][0]["kind"] == "dataset"
    assert version["sources"][0]["id"] == "lahman"
    assert version["computation"]["inline"]
    assert version["parameters"]["lahman.playerID"] == "aaronha01"
    assert version["parameters"]["warehouse"] == "warehouse/lahman.sqlite"
    assert version["parameters"]["attribute"] == "birth_date"
    assert version["actor"]["specialist"] == "bio_specialist"
    inline = version["computation"]["inline"]
    assert "birthYear" in inline
    assert "people_compose_iso_date" in inline or "birthMonth" in inline


@pytest.mark.smoke
def test_birth_date_cache_hit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _refresh_baseball_root(tmp_path, monkeypatch)
    _, first = _deliver_birth_date()
    _, second = _deliver_birth_date()
    assert first.results[0].get("birth_date") == "1934-02-05"
    assert second.results[0].get("birth_date") == "1934-02-05"
    assert (root / "agents" / "bio" / "storage.json").is_file()


@pytest.mark.smoke
def test_birth_date_missing_birth_month_na(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _refresh_baseball_root(
        tmp_path,
        monkeypatch,
        fixture_fn=_write_missing_birth_month_fixture,
    )
    _, response = _deliver_birth_date()
    assert response.results
    assert response.results[0].get("birth_date") == "N/A"


def _write_bats_fixture(seed_dir: Path) -> None:
    _write_minimal_lahman_fixture(seed_dir)
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut,bats,throws\n"
        "1,aaronha01,Hank,Aaron,1934,2,5,,L,R\n",
        encoding="utf-8",
    )


@pytest.mark.smoke
def test_bats_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _refresh_baseball_root(
        tmp_path,
        monkeypatch,
        fixture_fn=_write_bats_fixture,
    )
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=["bats"],
    )
    r1 = run_query(step1, thread_id="bats-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="bats-step2",
    )
    assert r2.outcome in {"found", "assembled"}
    assert r2.results
    assert r2.results[0].get("bats") == "L"


def _deliver_bio_attr(
    attr: str,
    *,
    provenance: bool = False,
) -> tuple[object, object]:
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=[attr],
        provenance=provenance,
    )
    r1 = run_query(step1, thread_id=f"{attr}-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id=f"{attr}-step2",
    )
    return r1, r2


@pytest.mark.smoke
def test_height_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_shared_fixture(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("height")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert response.results[0].get("height") == "72"


@pytest.mark.smoke
def test_weight_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_shared_fixture(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("weight")
    assert response.results
    assert response.results[0].get("weight") == "180"


@pytest.mark.smoke
def test_birth_country_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_shared_fixture(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("birth_country")
    assert response.results
    assert response.results[0].get("birth_country") == "USA"


@pytest.mark.smoke
def test_final_game_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_shared_fixture(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("final_game")
    assert response.results
    assert response.results[0].get("final_game") == "1976-10-03"


@pytest.mark.smoke
def test_death_date_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_shared_fixture(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("death_date")
    assert response.results
    assert response.results[0].get("death_date") == "2021-01-22"

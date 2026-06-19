"""End-to-end career_avg derive with mocked LLM codegen."""

from __future__ import annotations

import importlib.util
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
from baseball_derive_fixtures import (
    CAREER_AVG_DERIVE_BAD_SOURCE,
    CAREER_AVG_DERIVE_SOURCE,
)

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


def _load_derive_module(root: Path):
    live_loader = root / "specialists" / "specialist_loader.py"
    spec = importlib.util.spec_from_file_location(
        "_live_specialist_loader",
        live_loader,
    )
    assert spec is not None and spec.loader is not None
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    return loader.load_derive_resolve()


def _patch_derive_llm(monkeypatch: pytest.MonkeyPatch, dr, *, counter: dict | None = None):
    def fake_invoke(prompt, *, llm_invoke=None):
        if counter is not None:
            counter["count"] = counter.get("count", 0) + 1
        return CAREER_AVG_DERIVE_SOURCE.strip()

    monkeypatch.setattr(dr, "invoke_llm_for_prompt", fake_invoke)


def _patch_derive_llm_sequence(monkeypatch: pytest.MonkeyPatch, dr, sources: list[str]):
    state = {"index": 0}

    def fake_invoke(prompt, *, llm_invoke=None):
        idx = min(state["index"], len(sources) - 1)
        state["index"] += 1
        return sources[idx].strip()

    monkeypatch.setattr(dr, "invoke_llm_for_prompt", fake_invoke)


def _deliver_career_avg(*, provenance: bool = False) -> tuple[object, object]:
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=["career_avg"],
        provenance=provenance,
    )
    r1 = run_query(step1, thread_id="career-avg-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    step2 = EntityQuery(delivery_id=r1.delivery.delivery_id)
    r2 = run_query(step2, thread_id="career-avg-step2")
    return r1, r2


@pytest.mark.smoke
def test_career_avg_derive_mocked_llm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _refresh_baseball_root(tmp_path, monkeypatch)
    dr = _load_derive_module(root)
    _patch_derive_llm(monkeypatch, dr)

    _, response = _deliver_career_avg()
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert str(response.results[0].get("career_avg")) == "0.500"


@pytest.mark.smoke
def test_career_avg_derive_provenance_and_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _refresh_baseball_root(tmp_path, monkeypatch)
    dr = _load_derive_module(root)
    _patch_derive_llm(monkeypatch, dr)

    _, first = _deliver_career_avg(provenance=True)
    assert first.provenance is not None
    version = first.provenance["entities"][0]["attributes"]["career_avg"]["versions"][0]
    assert version["status"] == "found"
    assert version["value"] == "0.500"
    assert "query_warehouse" in version["computation"]["inline"]
    assert version["parameters"]["warehouse"] == "warehouse/lahman.sqlite"
    assert version["parameters"]["attribute"] == "career_avg"

    counter: dict[str, int] = {}
    _patch_derive_llm(monkeypatch, dr, counter=counter)
    _, second = _deliver_career_avg()
    assert str(second.results[0].get("career_avg")) == "0.500"
    assert counter.get("count", 0) == 0


@pytest.mark.smoke
def test_career_avg_derive_retries_after_sqlite_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _refresh_baseball_root(tmp_path, monkeypatch)
    dr = _load_derive_module(root)
    _patch_derive_llm_sequence(
        monkeypatch,
        dr,
        [CAREER_AVG_DERIVE_BAD_SOURCE, CAREER_AVG_DERIVE_SOURCE],
    )

    _, response = _deliver_career_avg()
    assert response.outcome in {"found", "assembled"}
    assert str(response.results[0].get("career_avg")) == "0.500"


@pytest.mark.smoke
def test_career_avg_derive_exhausts_attempts_to_na(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_DERIVE_MAX_ATTEMPTS", "5")
    root = _refresh_baseball_root(tmp_path, monkeypatch)
    dr = _load_derive_module(root)
    counter: dict[str, int] = {}

    def always_bad(prompt, *, llm_invoke=None):
        counter["count"] = counter.get("count", 0) + 1
        return CAREER_AVG_DERIVE_BAD_SOURCE.strip()

    monkeypatch.setattr(dr, "invoke_llm_for_prompt", always_bad)

    _, response = _deliver_career_avg()
    assert response.results
    assert response.results[0].get("career_avg") in {"N/A", "pending", None, ""}
    assert counter.get("count", 0) == 5

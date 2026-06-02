"""Tests for core Mycelium graph and storage (query-only public paths)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.core_identity import reset_core_identity
from graphs.core import reset_core_graph, run_query
from models.state import PersonQuery
from storage.core import CoreStorage, reset_storage


@pytest.fixture
def temp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CoreStorage:
    reset_storage()
    reset_core_identity()
    reset_core_graph()
    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "people": [
                    {
                        "id": "person-test",
                        "name": "Test User",
                        "employer": "Test Co",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    from storage.core import get_storage

    storage = get_storage()
    yield storage
    reset_storage()
    reset_core_identity()
    reset_core_graph()


@pytest.mark.full
def test_query_existing_person(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(PersonQuery(person_key="person-test"))
    assert len(response.results) == 1
    assert response.results[0]["name"] == "Test User"
    assert response.results[0]["employer"] == "Test Co"
    assert "Found core record" in response.message
    assert "person_key='person-test'" in response.debug


@pytest.mark.full
def test_query_missing_person(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(PersonQuery(person_key="Missing Person"))
    assert response.results == []
    assert "No core record found" in response.message
    assert "did not match" in response.message.lower()
    assert "outcome='not_found'" in response.debug


@pytest.mark.full
def test_query_non_core_attributes(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(
        PersonQuery(
            person_key="person-test",
            requested_attributes=["age", "x_handle"],
        ),
    )
    assert len(response.results) == 1
    assert response.results[0]["name"] == "Test User"
    assert "still researching" in response.message
    assert "age" in response.message
    assert "x_handle" in response.message
    assert "non_core_requested='age, x_handle'" in response.debug


@pytest.mark.full
def test_results_are_plain_dicts(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(PersonQuery(person_key="person-test"))
    for item in response.results:
        assert isinstance(item, dict)
        assert set(item.keys()) <= {"id", "name", "employer"}


@pytest.mark.full
def test_run_query_echoes_thread_id_on_lookup(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(
        PersonQuery(person_key="person-test"),
        thread_id="thread-lookup-1",
    )
    assert response.thread_id == "thread-lookup-1"
    assert response.trace_id is None


@pytest.mark.full
def test_run_query_default_thread_id(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(PersonQuery(person_key="person-test"))
    assert response.thread_id == "default"
    assert response.trace_id is None


@pytest.mark.full
def test_graph_invokes_supervisor_then_core_data(temp_storage: CoreStorage) -> None:
    """End-to-end graph path after 1070: supervisor routes, core_data responds."""
    import asyncio

    from graphs.core import build_core_graph
    from models.state import MyceliumGraphState

    _ = temp_storage
    graph = build_core_graph()
    initial = MyceliumGraphState(
        query=PersonQuery(person_key="person-test"),
        invocation_thread_id="graph-path-test",
    )
    final = asyncio.run(
        graph.ainvoke(
            initial,
            config={"configurable": {"thread_id": "graph-path-test"}},
        ),
    )
    state = (
        final
        if isinstance(final, MyceliumGraphState)
        else MyceliumGraphState.model_validate(final)
    )

    assert state.response is not None
    assert len(state.response.results) == 1
    assert "Found core record" in state.response.message
    joined_logs = " ".join(state.audit_log)
    assert "Supervisor" in joined_logs
    assert "routing to core_data" in joined_logs
    assert "CoreDataAgent" in joined_logs

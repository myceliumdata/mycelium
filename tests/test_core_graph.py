"""Tests for core Mycelium graph and storage (query-only public paths)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.core_identity import reset_core_identity
from agents.seed import get_seed_data, reset_seed_data
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from storage.core import CoreStorage, reset_storage


@pytest.fixture
def temp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CoreStorage:
    reset_storage()
    reset_seed_data()
    reset_context_builder()
    reset_core_identity()
    reset_core_graph()
    reset_category_tree()
    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "people": [
                    {
                        "name": "Test User",
                        "employer": "Test Co",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    (tmp_path / "network.json").write_text(
        json.dumps(
            {
                "name": "crm",
                "mvr": {
                    "bind_fields": ["name", "employer"],
                    "name_source": "entity_key",
                },
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(tmp_path / "categories.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry
    from storage.core import get_storage

    reset_agent_registry()
    reset_agent_factory()
    storage = get_storage()
    storage.seed_from_file(seed)
    reset_seed_data()
    _ = get_seed_data()
    yield storage
    reset_storage()
    reset_seed_data()
    reset_context_builder()
    reset_core_identity()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.full
def test_query_existing_person(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(EntityQuery(entity_key="Test User"))
    assert len(response.results) == 1
    assert response.results[0]["name"] == "Test User"
    assert response.results[0]["employer"] == "Test Co"
    pid = response.results[0]["id"]
    assert pid
    assert len(pid.split("-")) == 5
    assert len(pid.split("-")) == 5
    assert "Found record for" in response.message
    assert "core record" not in response.message.lower()
    assert "entity_key='Test User'" in response.debug


@pytest.mark.full
def test_query_missing_person(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(EntityQuery(entity_key="Missing Person"))
    assert response.results == []
    assert response.outcome == "entity_unknown"
    assert response.required_fields == ["employer"]
    assert "Missing Person" in response.message
    assert "employer" in response.message.lower()
    assert "core record" not in response.message.lower()
    assert "outcome='entity_unknown'" in response.debug


@pytest.mark.full
def test_query_non_core_attributes(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(
        EntityQuery(
            entity_key="Test User",
            requested_attributes=["age", "x_handle"],
        ),
    )
    assert len(response.results) == 1
    assert "name" not in response.results[0]
    assert "employer" not in response.results[0]
    assert response.results[0]["id"]
    assert "Classified age as demographic" in response.message
    assert "researching" in response.message.lower()
    assert "Classified x_handle as social" in response.message
    assert "x_handle" in response.message
    assert "contributions=2" in response.debug
    assert "outcome='assembled'" in response.debug


@pytest.mark.full
def test_results_are_plain_dicts(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(EntityQuery(entity_key="Test User"))
    for item in response.results:
        assert isinstance(item, dict)
        assert set(item.keys()) <= {"id", "name", "employer"}
        assert item.get("id")


@pytest.mark.full
def test_run_query_echoes_thread_id_on_lookup(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(
        EntityQuery(entity_key="Test User"),
        thread_id="thread-lookup-1",
    )
    assert response.thread_id == "thread-lookup-1"
    assert response.trace_id is None


@pytest.mark.full
def test_run_query_default_thread_id(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(EntityQuery(entity_key="Test User"))
    assert response.thread_id == "default"
    assert response.trace_id is None


@pytest.mark.full
def test_graph_invokes_supervisor_assemble_response(temp_storage: CoreStorage) -> None:
    """End-to-end graph: supervisor + assemble_response for name-only query."""
    import asyncio

    from graphs.core import build_core_graph
    from models.state import MyceliumGraphState

    _ = temp_storage
    graph = build_core_graph(setup_checkpointer=False)
    initial = MyceliumGraphState(
        query=EntityQuery(entity_key="Test User"),
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
    assert "Found record for" in state.response.message
    assert "core record" not in state.response.message.lower()
    joined_logs = " ".join(state.audit_log)
    assert "Supervisor" in joined_logs
    assert "assemble_response" in joined_logs
    assert state.route is None

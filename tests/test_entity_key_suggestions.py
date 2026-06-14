"""Smoke tests for entity key near-miss suggestions (entity protocol slice 1)."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import reset_entity_registry
from agents.entity_resolution import resolve_entity_key
from graphs.core import reset_core_graph, run_query
from network_helpers import import_seed_for_test
from models.state import EntityQuery
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_seed_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """Isolated network with CRM example seed and sample ontology."""
    reset_storage()
    reset_entity_registry()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()

    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)

    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_category_tree()
    from agents.classification import get_category_tree

    get_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    storage = get_storage()
    import_seed_for_test(seed)

    yield storage

    reset_storage()
    reset_entity_registry()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_resolve_kalman_suggests_kalmans(crm_seed_env: CoreStorage) -> None:
    resolution = resolve_entity_key("Andrea Kalman")
    assert resolution.kind == "suggest"
    assert len(resolution.suggestions) == 1
    assert resolution.suggestions[0].suggested_lookup == {"name": "Andrea Kalmans"}
    assert resolution.suggestions[0].employer == "Lontra Ventures"
    assert resolution.suggestions[0].score >= 0.85


@pytest.mark.smoke
def test_andrea_kalman_email_unresolved_no_specialist_invoke(
    crm_seed_env: CoreStorage,
) -> None:
    response = run_query(
        EntityQuery(entity_key="Andrea Kalman", requested_attributes=["email"]),
    )

    assert response.outcome == "entity_key_unresolved"
    assert response.results == []
    assert len(response.suggestions) == 1
    assert response.suggestions[0].suggested_lookup == {"name": "Andrea Kalmans"}
    assert "Andrea Kalmans" in response.message
    assert "Lontra Ventures" in response.message
    assert "outcome='entity_key_unresolved'" in response.debug
    from agents.supervisor import supervisor_agent
    from models.state import MyceliumGraphState

    planned = supervisor_agent(
        MyceliumGraphState(
            query=EntityQuery(entity_key="Andrea Kalman", requested_attributes=["email"]),
        ),
    )
    assert planned["context"]["_meta"]["specialists_to_invoke"] == []


@pytest.mark.smoke
def test_andrea_kalmans_not_unresolved(crm_seed_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(entity_key="Andrea Kalmans", requested_attributes=["email"]),
    )

    assert response.outcome != "entity_key_unresolved"
    assert response.suggestions == []


@pytest.mark.smoke
def test_unknown_entity_entity_unknown_empty_suggestions(crm_seed_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(
            entity_key="NoSuchPerson-xyz",
            requested_attributes=["email"],
        ),
    )

    assert response.outcome == "entity_unknown"
    assert response.required_fields == ["employer"]
    assert response.suggestions == []
    assert response.results == []


@pytest.mark.smoke
def test_uuid_miss_no_suggestions(crm_seed_env: CoreStorage) -> None:
    missing_id = str(uuid.uuid4())
    resolution = resolve_entity_key(missing_id)
    assert resolution.kind == "none"
    assert resolution.suggestions == []

    response = run_query(
        EntityQuery(entity_key=missing_id, requested_attributes=["email"]),
    )
    assert response.outcome == "not_found"
    assert response.suggestions == []


@pytest.mark.smoke
def test_same_thread_retry_after_unresolved_no_serde_warning(
    crm_seed_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Same thread_id: unresolved then exact retry must not break checkpoint serde."""
    _ = crm_seed_env
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()
    caplog.set_level("WARNING")
    thread_id = "entity-suggest-retry-thread"

    first = run_query(
        EntityQuery(entity_key="Andrea Kalman", requested_attributes=["email"]),
        thread_id=thread_id,
    )
    assert first.outcome == "entity_key_unresolved"
    assert len(first.suggestions) == 1

    second = run_query(
        EntityQuery(entity_key="Andrea Kalmans", requested_attributes=["email"]),
        thread_id=thread_id,
    )
    assert second.outcome != "entity_key_unresolved"
    assert second.suggestions == []

    serde_warnings = [
        record.message
        for record in caplog.records
        if "LookupSuggestion" in record.message
        or "Blocked deserialization" in record.message
    ]
    assert serde_warnings == []


@pytest.mark.smoke
def test_kevin_zhang_multiple_exact_not_suggest(crm_seed_env: CoreStorage) -> None:
    resolution = resolve_entity_key("Kevin Zhang")
    assert resolution.kind == "multiple"
    assert resolution.suggestions == []

    response = run_query(
        EntityQuery(entity_key="Kevin Zhang", requested_attributes=["email"]),
    )
    assert response.outcome != "entity_key_unresolved"
    assert response.suggestions == []
    assert len(response.results) == 2
    assert "Found 2 records for 'Kevin Zhang'." in response.message

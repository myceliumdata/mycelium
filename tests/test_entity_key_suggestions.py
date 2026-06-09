"""Smoke tests for entity key near-miss suggestions (entity protocol slice 1)."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.core_identity import reset_core_identity
from agents.entity_resolution import resolve_entity_key
from agents.seed import get_seed_data, reset_seed_data
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm" / "seed.json"


@pytest.fixture
def crm_seed_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """Isolated network with CRM example seed and sample ontology."""
    reset_storage()
    reset_seed_data()
    reset_context_builder()
    reset_core_identity()
    reset_core_graph()
    reset_category_tree()

    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)

    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
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


@pytest.mark.smoke
def test_resolve_kalman_suggests_kalmans(crm_seed_env: CoreStorage) -> None:
    resolution = resolve_entity_key("Andrea Kalman")
    assert resolution.kind == "suggest"
    assert len(resolution.suggestions) == 1
    assert resolution.suggestions[0].entity_key == "Andrea Kalmans"
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
    assert response.suggestions[0].entity_key == "Andrea Kalmans"
    assert "Andrea Kalmans" in response.message
    assert "Lontra Ventures" in response.message
    assert "invoke_specialists" not in response.debug
    assert "outcome='entity_key_unresolved'" in response.debug


@pytest.mark.smoke
def test_andrea_kalmans_not_unresolved(crm_seed_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(entity_key="Andrea Kalmans", requested_attributes=["email"]),
    )

    assert response.outcome != "entity_key_unresolved"
    assert response.suggestions == []


@pytest.mark.smoke
def test_unknown_entity_not_found_empty_suggestions(crm_seed_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(
            entity_key="NoSuchPerson-xyz",
            requested_attributes=["email"],
        ),
    )

    assert response.outcome == "not_found"
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

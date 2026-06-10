"""Smoke tests for MVR validation orchestration (entity protocol slice 5)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import get_entity_registry, reset_entity_registry
from graphs.core import reset_core_graph, run_query
from network_helpers import import_seed_for_test
from models.state import EntityQuery
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_validation_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
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
    _ = get_entity_registry()
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()

    yield storage

    reset_storage()
    reset_entity_registry()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


def _entities_path() -> Path:
    return Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"])


@pytest.mark.smoke
def test_provisional_murphy_validates_identity_only(crm_validation_env: CoreStorage) -> None:
    _ = crm_validation_env
    response = run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"}),
    )

    assert response.outcome == "entity_validated"
    assert response.message == "Core record validated."
    assert response.results[0]["employer"] == "Acme Corp"
    payload = json.loads(_entities_path().read_text(encoding="utf-8"))
    entity = payload["entities"][response.results[0]["id"]]
    assert entity["validation_state"] == "validated"
    assert entity["field_states"]["name"] == "validated"
    assert entity["field_states"]["employer"] == "validated"


@pytest.mark.smoke
def test_requery_after_bind_validates_same_turn(crm_validation_env: CoreStorage) -> None:
    _ = crm_validation_env
    first = run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"}),
    )
    assert first.outcome == "entity_validated"
    entity_id = first.results[0]["id"]

    second = run_query(EntityQuery(entity_key=entity_id))
    assert second.outcome == "found"
    assert "Core record validated" not in second.message


@pytest.mark.smoke
def test_absurd_employer_fails_validation_stays_provisional(
    crm_validation_env: CoreStorage,
) -> None:
    _ = crm_validation_env
    response = run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "A"}),
    )

    assert response.outcome == "found"
    assert "validation failed" in response.message.lower()
    assert "employer" in response.message.lower()
    payload = json.loads(_entities_path().read_text(encoding="utf-8"))
    entity = payload["entities"][response.results[0]["id"]]
    assert entity["validation_state"] == "provisional"


@pytest.mark.smoke
def test_seed_andrea_kalmans_no_validation_invoke(crm_validation_env: CoreStorage) -> None:
    _ = crm_validation_env
    response = run_query(
        EntityQuery(entity_key="Andrea Kalmans", requested_attributes=["email"]),
    )

    assert response.outcome == "assembled"
    assert "validate_entity" not in response.debug


@pytest.mark.smoke
def test_murphy_bind_plus_email_validates_then_assembles_same_turn(
    crm_validation_env: CoreStorage,
) -> None:
    _ = crm_validation_env
    response = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )

    assert response.outcome == "assembled"
    assert "entity_validated" not in response.outcome
    payload = json.loads(_entities_path().read_text(encoding="utf-8"))
    entity = payload["entities"][response.results[0]["id"]]
    assert entity["validation_state"] == "validated"

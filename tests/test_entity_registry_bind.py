"""Smoke tests for entity registry + provisional bind (entity protocol slice 4)."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.core_identity import reset_core_identity
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.entity_resolution import resolve_entity
from agents.seed import reset_seed_data
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_registry_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """Isolated CRM network with MVR and empty entities.json."""
    reset_storage()
    reset_seed_data()
    reset_entity_registry()
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
    storage.seed_from_file(seed)
    reset_seed_data()
    reset_entity_registry()
    _ = get_entity_registry()
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()

    yield storage

    reset_storage()
    reset_seed_data()
    reset_entity_registry()
    reset_context_builder()
    reset_core_identity()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_murphy_bind_creates_provisional_entity(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    entities_path = Path(
        __import__("os").environ["MYCELIUM_ENTITIES_PATH"],
    )

    response = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
        ),
    )

    assert response.outcome == "entity_validated"
    assert response.required_fields == []
    assert len(response.results) == 1
    assert response.results[0]["name"] == "Paul Murphy"
    assert response.results[0]["employer"] == "Acme Corp"
    assert response.results[0]["id"]
    assert response.message == "Core record validated."
    assert entities_path.is_file()
    payload = json.loads(entities_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 1
    assert "paul murphy|acme corp" in payload["bind_index"]


@pytest.mark.smoke
def test_repeat_bind_is_idempotent_found(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    query = EntityQuery(
        entity_key="Paul Murphy",
        binding={"employer": "Acme Corp"},
    )

    first = run_query(query)
    assert first.outcome == "entity_validated"
    first_id = first.results[0]["id"]

    second = run_query(query)
    assert second.outcome == "found"
    assert second.results[0]["id"] == first_id

    entities_path = Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"])
    payload = json.loads(entities_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 1


@pytest.mark.smoke
def test_same_name_different_employers_get_two_ids(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env

    acme = run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"}),
    )
    beta = run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "Beta LLC"}),
    )

    assert acme.outcome == "entity_validated"
    assert beta.outcome == "entity_validated"
    assert acme.results[0]["id"] != beta.results[0]["id"]

    payload = json.loads(
        Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"]).read_text(),
    )
    assert len(payload["entities"]) == 2


@pytest.mark.smoke
def test_murphy_bound_plus_email_no_specialist_invoke(
    crm_registry_env: CoreStorage,
) -> None:
    _ = crm_registry_env
    bound = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert bound.outcome == "assembled"
    assert bound.results[0]["id"]
    payload = json.loads(
        Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"]).read_text(),
    )
    entity = next(iter(payload["entities"].values()))
    assert entity["validation_state"] == "validated"

    entity_id = bound.results[0]["id"]
    follow_up = run_query(
        EntityQuery(entity_key=entity_id, requested_attributes=["email"]),
    )
    assert follow_up.outcome == "assembled"
    assert follow_up.results[0]["id"] == entity_id


@pytest.mark.smoke
def test_aaron_holiday_seed_path_no_registry_write(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    entities_path = Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"])

    response = run_query(
        EntityQuery(entity_key="Aaron Holiday", requested_attributes=["email"]),
    )

    assert response.outcome == "assembled"
    assert not entities_path.exists() or json.loads(
        entities_path.read_text(encoding="utf-8"),
    ).get("entities") == {}


@pytest.mark.smoke
def test_partial_binding_under_specified(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    response = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": ""},
            requested_attributes=["email"],
        ),
    )

    assert response.outcome == "entity_under_specified"
    assert response.required_fields == ["employer"]
    assert response.results == []


@pytest.mark.smoke
def test_uuid_lookup_after_bind(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    bound = run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"}),
    )
    entity_id = bound.results[0]["id"]

    resolution = resolve_entity(EntityQuery(entity_key=entity_id))
    assert resolution.kind == "exact"
    assert resolution.matches[0]["id"] == entity_id


@pytest.mark.smoke
def test_bind_index_lookup_by_name_and_binding(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    bound = run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"}),
    )
    entity_id = bound.results[0]["id"]

    by_name = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
        ),
    )
    assert by_name.outcome == "found"
    assert by_name.results[0]["id"] == entity_id


@pytest.mark.smoke
def test_unknown_binding_keys_ignored(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    response = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp", "malicious": "x"},
        ),
    )
    assert response.outcome == "entity_validated"


@pytest.mark.smoke
def test_missing_uuid_stays_not_found(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    missing_id = str(uuid.uuid4())
    response = run_query(EntityQuery(entity_key=missing_id))
    assert response.outcome == "not_found"

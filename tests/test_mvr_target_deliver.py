"""Smoke tests: MVR redesign M5 — step-2 deliver via delivery_id."""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import get_entity_registry, reset_entity_registry
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import get_delivery_store, issue_delivery, reset_delivery_store
from network_helpers import import_seed_for_test
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_deliver_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()

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
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(tmp_path / "deliveries.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_category_tree()
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
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_step1_step2_identity_roundtrip(crm_deliver_env: CoreStorage) -> None:
    _ = crm_deliver_env
    registry = get_entity_registry()
    entity_ids = registry.lookup_by_target_lookup(
        {"name": "Nichanan Kesonpat", "employer": "1k(x)"},
    )
    assert len(entity_ids) == 1

    step1 = run_query(EntityQuery(id=entity_ids[0]))
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert len(step2.results) == 1
    assert step2.results[0]["name"] == "Nichanan Kesonpat"
    assert step2.delivery is None
    assert step2.total_matches is None


@pytest.mark.smoke
def test_step2_multi_match_delivery(crm_deliver_env: CoreStorage) -> None:
    _ = crm_deliver_env
    step1 = run_query(EntityQuery(lookup={"employer": "645 Ventures"}))
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 3
    assert step1.delivery is not None

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert len(step2.results) == 3
    names = {row["name"] for row in step2.results}
    assert names == {"Aaron Holiday", "Nnamdi Okike", "Vardan Gattani"}


@pytest.mark.smoke
def test_step2_with_bound_attributes_assembled(crm_deliver_env: CoreStorage) -> None:
    _ = crm_deliver_env
    registry = get_entity_registry()
    entity_ids = registry.lookup_by_target_lookup(
        {"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
    )
    assert len(entity_ids) == 1

    step1 = run_query(
        EntityQuery(
            id=entity_ids[0],
            requested_attributes=["email"],
        ),
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "assembled"
    assert len(step2.results) == 1
    assert step2.results[0]["id"] == entity_ids[0]


@pytest.mark.smoke
def test_expired_delivery_id_not_found(crm_deliver_env: CoreStorage) -> None:
    _ = crm_deliver_env
    registry = get_entity_registry()
    entity_ids = registry.lookup_by_target_lookup({"employer": "Accel"})
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    scope = issue_delivery(
        entity_ids=entity_ids,
        lookup={"employer": "Accel"},
        now=past,
    )
    get_delivery_store().put(scope)

    response = run_query(EntityQuery(delivery_id=scope.delivery_id))
    assert response.outcome == "not_found"
    assert response.results == []
    assert response.delivery is None


@pytest.mark.smoke
def test_unknown_delivery_id_not_found(crm_deliver_env: CoreStorage) -> None:
    _ = crm_deliver_env
    response = run_query(EntityQuery(delivery_id="d_doesnotexist"))
    assert response.outcome == "not_found"
    assert "No valid delivery" in response.message


@pytest.mark.smoke
def test_legacy_entity_key_unaffected_by_deliver_path(crm_deliver_env: CoreStorage) -> None:
    _ = crm_deliver_env
    response = run_query(EntityQuery(entity_key="Nichanan Kesonpat"))
    assert response.outcome == "found"
    assert response.results
    assert response.delivery is None


@pytest.mark.smoke
def test_step2_deliver_serializes_without_delivery_fields(crm_deliver_env: CoreStorage) -> None:
    _ = crm_deliver_env
    step1 = run_query(EntityQuery(lookup={"employer": "Accel"}))
    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    payload = step2.public_dict()
    assert payload["outcome"] == "found"
    assert payload["results"]
    assert "total_matches" not in payload
    assert "delivery" not in payload
    assert "quote" not in payload

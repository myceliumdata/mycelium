"""Smoke tests: empty-crm create-on-deliver without upfront MVR category bootstrap."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.classification.engine import _SEED_CATEGORIES
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from agents.specialists.base import SpecialistStorage
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import get_delivery_store, reset_delivery_store
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_EMPTY_CRM = REPO_ROOT / "examples" / "networks" / "empty-crm"


@pytest.fixture
def empty_crm_create_on_deliver_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """No-seed network: categories bootstrapped on step 1 without MVR bind mappings."""
    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()

    shutil.copy(EXAMPLE_EMPTY_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(tmp_path / "categories.json"))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(tmp_path / "deliveries.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("MYCELIUM_SEED_PATH", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    categories_path = tmp_path / "categories.json"
    categories_path.write_text(
        json.dumps(_SEED_CATEGORIES, indent=2) + "\n",
        encoding="utf-8",
    )
    assert not (tmp_path / "seed.json").exists()
    attr_map = _SEED_CATEGORIES.get("attribute_map") or {}
    assert attr_map.get("name") is None
    assert attr_map.get("employer") is None

    reset_category_tree()
    storage = get_storage()
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()
    yield storage

    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_empty_crm_step2_bind_without_upfront_mvr_mappings(
    empty_crm_create_on_deliver_env: CoreStorage,
) -> None:
    """Reproduce empty-crm gap: classification seed lacks name/employer in attribute_map."""
    _ = empty_crm_create_on_deliver_env
    lookup = {"name": "Paul Murphy", "employer": "Acme Corp"}
    categories_file = Path(os.environ["MYCELIUM_CATEGORIES_PATH"])

    step1 = run_query(EntityQuery(lookup=lookup))
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 0
    assert step1.delivery is not None
    assert step1.delivery.create_on_deliver is True

    categories = json.loads(categories_file.read_text(encoding="utf-8"))
    attr_map = categories.get("attribute_map") or {}
    assert attr_map.get("name") is None
    assert attr_map.get("employer") is None

    stored = get_delivery_store().get(step1.delivery.delivery_id)
    assert stored is not None
    assert stored.create_on_deliver is True
    assert stored.entity_ids == []

    registry = get_entity_registry()
    before_ids = {entity.id for entity in registry.list_entities()}

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert len(step2.results) == 1
    created = step2.results[0]
    assert created["id"] not in before_ids
    assert created["name"] == "Paul Murphy"
    assert created["employer"] == "Acme Corp"

    categories_after = json.loads(categories_file.read_text(encoding="utf-8"))
    attr_after = categories_after.get("attribute_map") or {}
    assert attr_after.get("name") == "demographic"
    assert attr_after.get("employer") == "professional"

    demographic = SpecialistStorage("demographic")
    professional = SpecialistStorage("professional")
    demo_records = demographic.load().get("records") or {}
    prof_records = professional.load().get("records") or {}
    assert len(demo_records) == 1
    assert len(prof_records) == 1
    entity_id = created["id"]
    name_entry = demo_records[entity_id]["name"]
    employer_entry = prof_records[entity_id]["employer"]
    assert name_entry["versions"][0]["actor"]["kind"] == "bind"
    assert employer_entry["versions"][0]["actor"]["kind"] == "bind"

"""Smoke tests: MVR redesign M7 — create-on-deliver + name_source retirement."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
from agents.classification import get_category_tree, reset_category_tree
from agents.registry import reset_agent_registry
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import get_delivery_store, reset_delivery_store
from network.mvr import load_mvr
from network_helpers import import_seed_for_test
from storage.core import CoreStorage, get_storage, reset_storage
from tools.research import ResearchRunResult
from versioned_storage_fixtures import versioned_found

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


def _mock_email_research(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        storage: Any,
        llm: Any | None = None,
    ) -> ResearchRunResult:
        _ = category, specialist_name, context, llm
        calls.append(person_id)
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        for field in target_fields:
            rec[field] = versioned_found(
                at=now,
                value="new.person@example.com",
                confidence=0.9,
                sources=["https://example.com/new"],
                category="contact",
                specialist_name="contact_specialist",
            )
        storage.save(data)
        return ResearchRunResult(fields_updated=list(target_fields), tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)
    return calls


@pytest.fixture
def crm_create_on_deliver_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()

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
    get_agent_factory().create_specialist(
        "contact",
        "contact_specialist",
        "Direct contact info",
        examples=["email", "phone"],
        auto_commit=False,
    )
    storage = get_storage()
    import_seed_for_test(seed)
    _ = get_entity_registry()
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
def test_partial_lookup_zero_matches_not_found(
    crm_create_on_deliver_env: CoreStorage,
) -> None:
    _ = crm_create_on_deliver_env
    response = run_query(
        EntityQuery(
            lookup={"employer": "Totally Unknown Corp"},
            requested_attributes=["email"],
        ),
    )
    assert response.outcome == "not_found"
    assert response.delivery is None
    assert "No records found" in response.message


@pytest.mark.smoke
def test_full_mvr_zero_matches_without_attrs_create_on_deliver(
    crm_create_on_deliver_env: CoreStorage,
) -> None:
    _ = crm_create_on_deliver_env
    lookup = {"name": "Brand New Person", "employer": "Never Seen Inc"}
    step1 = run_query(EntityQuery(lookup=lookup))
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 0
    assert step1.delivery is not None

    stored = get_delivery_store().get(step1.delivery.delivery_id)
    assert stored is not None
    assert stored.create_on_deliver is True
    assert stored.requested_attributes == []

    registry = get_entity_registry()
    before_ids = {entity.id for entity in registry.list_entities()}

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert len(step2.results) == 1
    created = step2.results[0]
    assert created["id"] not in before_ids
    assert created["name"] == "Brand New Person"
    assert created["employer"] == "Never Seen Inc"


@pytest.mark.smoke
def test_full_mvr_zero_matches_step1_delivery_step2_create(
    crm_create_on_deliver_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_create_on_deliver_env
    _mock_email_research(monkeypatch)
    lookup = {"name": "Brand New Person", "employer": "Never Seen Inc"}

    step1 = run_query(
        EntityQuery(lookup=lookup, requested_attributes=["email"]),
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 0
    assert step1.results == []
    assert step1.delivery is not None

    stored = get_delivery_store().get(step1.delivery.delivery_id)
    assert stored is not None
    assert stored.entity_ids == []
    assert stored.create_on_deliver is True
    assert stored.lookup == lookup
    assert stored.requested_attributes == ["email"]

    registry = get_entity_registry()
    before_ids = {entity.id for entity in registry.list_entities()}

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "assembled"
    assert len(step2.results) == 1
    created = step2.results[0]
    assert created["id"] not in before_ids
    assert created.get("email") == "new.person@example.com"

    entity = registry.lookup_by_id(created["id"])
    assert entity is not None
    assert entity.name == "Brand New Person"
    assert entity.employer == "Never Seen Inc"


@pytest.mark.smoke
def test_name_source_in_network_json_is_ignored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network = {
        "name": "legacy-mvr",
        "mvr": {
            "bind_fields": ["name", "employer"],
            "name_source": "entity_key",
            "description": "legacy field ignored",
        },
    }
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    (tmp_path / "network.json").write_text(json.dumps(network), encoding="utf-8")
    policy = load_mvr()
    assert policy.bind_fields == ["name", "employer"]
    summary = policy.summary()
    assert "name_source" not in summary

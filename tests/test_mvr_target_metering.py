"""Smoke tests: MVR redesign M6 — target protocol metering + quote_id."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agents.entity_registry import get_entity_registry, reset_entity_registry
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import reset_delivery_store
from network.entitlements import reset_entitlement_store
from network.quotes import reset_quote_store
from network_helpers import import_seed_for_test
from storage.core import CoreStorage, get_storage, reset_storage
from tools.research import ResearchRunResult

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


def _write_metering_network_json(
    path: Path,
    *,
    enabled: bool = True,
    **overrides: Any,
) -> None:
    data = json.loads((EXAMPLE_CRM / "network.json").read_text(encoding="utf-8"))
    metering = dict(data.get("metering") or {})
    metering["enabled"] = enabled
    metering.update(overrides)
    data["metering"] = metering
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


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
            rec[field] = {
                "status": "found",
                "value": "paul.murphy@acme.example",
                "confidence": 0.9,
                "sources": ["https://example.com/paul"],
                "researched_at": now,
            }
        storage.save(data)
        return ResearchRunResult(fields_updated=list(target_fields), tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)
    return calls


@pytest.fixture
def crm_target_metering_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_entitlement_store()
    reset_quote_store()
    reset_delivery_store()

    from agents.classification import get_category_tree, reset_category_tree
    from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
    from agents.registry import reset_agent_registry

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    _write_metering_network_json(tmp_path / "network.json", enabled=True)

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
    monkeypatch.setenv("MYCELIUM_ENTITLEMENTS_PATH", str(tmp_path / "entitlements.json"))
    monkeypatch.setenv("MYCELIUM_QUOTES_PATH", str(tmp_path / "quotes.json"))
    monkeypatch.setenv("MYCELIUM_METER_RESEARCH_USD", "2.0")
    monkeypatch.setenv("MYCELIUM_METER_QUERY_VALUE_USD", "0.05")
    monkeypatch.delenv("MYCELIUM_AUTO_ACCEPT_QUOTES", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_category_tree()
    get_category_tree()
    reset_agent_registry()
    reset_agent_factory()
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
    reset_entitlement_store()
    reset_quote_store()
    reset_delivery_store()


@pytest.mark.smoke
def test_metered_step1_with_attrs_quote_required(
    crm_target_metering_env: CoreStorage,
) -> None:
    _ = crm_target_metering_env
    registry = get_entity_registry()
    entity_ids = registry.lookup_by_target_lookup(
        {"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
    )
    assert len(entity_ids) == 1

    step1 = run_query(
        EntityQuery(id=entity_ids[0], requested_attributes=["email"]),
    )
    assert step1.outcome == "quote_required"
    assert step1.total_matches == 1
    assert step1.delivery is not None
    assert step1.quote is not None
    assert step1.quote["workload"]["delivery_id"] == step1.delivery.delivery_id
    assert step1.results == []


@pytest.mark.smoke
def test_metered_step2_without_quote_blocked(
    crm_target_metering_env: CoreStorage,
) -> None:
    _ = crm_target_metering_env
    step1 = run_query(EntityQuery(lookup={"employer": "Accel"}))
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "quote_required"
    assert step2.quote is not None
    assert step2.results == []


@pytest.mark.smoke
def test_metered_step1_step2_with_accepted_quote_delivers(
    crm_target_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_target_metering_env
    _mock_email_research(monkeypatch)
    registry = get_entity_registry()
    entity_ids = registry.lookup_by_target_lookup(
        {"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
    )

    step1 = run_query(
        EntityQuery(id=entity_ids[0], requested_attributes=["email"]),
    )
    assert step1.outcome == "quote_required"
    quote_id = step1.quote["quote_id"]
    delivery_id = step1.delivery.delivery_id

    step2 = run_query(
        EntityQuery(delivery_id=delivery_id, quote_id=quote_id),
    )
    assert step2.outcome == "assembled"
    assert len(step2.results) == 1
    assert step2.results[0]["id"] == entity_ids[0]


@pytest.mark.smoke
def test_metered_batch_step1_line_items_scale_with_entity_count(
    crm_target_metering_env: CoreStorage,
) -> None:
    _ = crm_target_metering_env
    step1 = run_query(
        EntityQuery(
            lookup={"employer": "645 Ventures"},
            requested_attributes=["email"],
        ),
    )
    assert step1.outcome == "quote_required"
    assert step1.total_matches == 3
    assert step1.quote is not None
    assert step1.quote["total_usd"] == pytest.approx(6.15)
    workload = step1.quote["workload"]
    assert workload["delivery_id"] == step1.delivery.delivery_id
    assert len(workload.get("entity_ids") or []) == 3


@pytest.mark.smoke
def test_free_network_target_protocol_without_quote(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-metered network: lookup_resolved → deliver without quote_id."""
    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_delivery_store()

    from agents.classification import get_category_tree, reset_category_tree

    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    shutil.copy(SAMPLE_CATEGORIES, tmp_path / "categories.json")
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(tmp_path / "categories.json"))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(tmp_path / "deliveries.json"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("MYCELIUM_AUTO_ACCEPT_QUOTES", raising=False)

    reset_category_tree()
    get_category_tree()
    import_seed_for_test(seed)
    reset_core_graph()

    step1 = run_query(EntityQuery(lookup={"employer": "Accel"}))
    assert step1.outcome == "lookup_resolved"
    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert step2.quote is None

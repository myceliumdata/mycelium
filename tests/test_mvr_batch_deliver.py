"""Smoke tests: MVR redesign M8 — batch step-2 deliver + batch provenance."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agents.attribute_write import bind_provisional
from agents.classification import get_category_tree, reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import get_entity_registry, reset_entity_registry
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import get_delivery_store, reset_delivery_store
from network.entitlements import reset_entitlement_store
from network.quotes import reset_quote_store
from network_helpers import import_seed_for_test
from storage.core import CoreStorage, get_storage, reset_storage
from tools.research import ResearchRunResult
from versioned_storage_fixtures import versioned_found

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


def _write_metering_network_json(path: Path, *, enabled: bool = True) -> None:
    data = json.loads((EXAMPLE_CRM / "network.json").read_text(encoding="utf-8"))
    metering = dict(data.get("metering") or {})
    metering["enabled"] = enabled
    data["metering"] = metering
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _mock_email_research(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    calls: dict[str, list[str]] = {}

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        llm: Any | None = None,
    ) -> ResearchRunResult:
        _ = category, specialist_name, context, llm
        calls.setdefault(person_id, []).extend(target_fields)
        from agents.specialists.base import SpecialistStorage

        storage = SpecialistStorage(category=category)
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        for field in target_fields:
            rec[field] = versioned_found(
                at=now,
                value=f"{person_id[:8]}@batch.example",
                confidence=0.9,
                sources=[f"https://example.com/{person_id[:8]}"],
                category="contact",
                specialist_name="contact_specialist",
            )
        storage.save(data)
        return ResearchRunResult(fields_updated=list(target_fields), tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)
    return calls


@pytest.fixture
def crm_batch_deliver_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()

    from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
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
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_batch_step2_deliver_with_attrs_researches_all_entities(
    crm_batch_deliver_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_batch_deliver_env
    calls = _mock_email_research(monkeypatch)

    step1 = run_query(
        EntityQuery(
            lookup={"employer": "645 Ventures"},
            requested_attributes=["email"],
        ),
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 3
    assert step1.delivery is not None

    stored = get_delivery_store().get(step1.delivery.delivery_id)
    assert stored is not None
    assert len(stored.entity_ids) == 3

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "assembled"
    assert len(step2.results) == 3
    result_ids = {row["id"] for row in step2.results}
    assert result_ids == set(stored.entity_ids)
    emails = {row["email"] for row in step2.results}
    assert len(emails) == 3
    assert all(str(email).endswith("@batch.example") for email in emails)
    assert len(calls) == 3


@pytest.mark.smoke
def test_batch_step2_provenance_entities_shape(
    crm_batch_deliver_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _ = crm_batch_deliver_env
    _mock_email_research(monkeypatch)

    step1 = run_query(
        EntityQuery(
            lookup={"employer": "645 Ventures"},
            requested_attributes=["email"],
            provenance=True,
        ),
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None

    stored = get_delivery_store().get(step1.delivery.delivery_id)
    assert stored is not None
    assert stored.provenance is True
    assert len(stored.entity_ids) == 3

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "assembled"
    assert len(step2.results) == 3
    assert step2.provenance is not None
    entities = step2.provenance.get("entities") or []
    assert len(entities) == 3
    provenance_ids = {item["id"] for item in entities}
    assert provenance_ids == set(stored.entity_ids)
    for item in entities:
        email_prov = (item.get("attributes") or {}).get("email")
        assert email_prov is not None
        assert email_prov.get("versions")


@pytest.mark.smoke
def test_multi_match_research_gate_returns_all_identity_rows(
    crm_batch_deliver_env: CoreStorage,
) -> None:
    """Research-gated batch deliver returns every scope identity row (M8 shape)."""
    _ = crm_batch_deliver_env
    registry = get_entity_registry()
    bad_row, _ = bind_provisional("Andrea Kalmans", "A", registry=registry)

    step1 = run_query(
        EntityQuery(
            lookup={"name": "Andrea Kalmans"},
            requested_attributes=["email"],
        ),
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 2
    assert step1.delivery is not None

    stored = get_delivery_store().get(step1.delivery.delivery_id)
    assert stored is not None
    assert len(stored.entity_ids) == 2
    assert bad_row.id in stored.entity_ids

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert len(step2.results) == 2
    result_ids = {row["id"] for row in step2.results}
    assert result_ids == set(stored.entity_ids)
    employers = {row.get("employer") for row in step2.results}
    assert "A" in employers
    assert "Lontra Ventures" in employers
    assert "provisional record for" not in step2.message.lower()
    assert "2 records" in step2.message
    assert "1 provisional row" in step2.message


@pytest.mark.smoke
def test_metered_batch_step1_step2_quote_roundtrip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_entitlement_store()
    reset_quote_store()
    reset_delivery_store()

    from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
    from agents.registry import reset_agent_registry

    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    shutil.copy(SAMPLE_CATEGORIES, tmp_path / "categories.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    _write_metering_network_json(tmp_path / "network.json", enabled=True)

    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
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
    import_seed_for_test(seed)
    _mock_email_research(monkeypatch)
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()

    step1 = run_query(
        EntityQuery(
            lookup={"employer": "645 Ventures"},
            requested_attributes=["email"],
        ),
    )
    assert step1.outcome == "quote_required"
    assert step1.total_matches == 3
    quote_id = step1.quote["quote_id"]
    delivery_id = step1.delivery.delivery_id

    step2 = run_query(EntityQuery(delivery_id=delivery_id, quote_id=quote_id))
    assert step2.outcome == "assembled"
    assert len(step2.results) == 3
    assert all(row.get("email") for row in step2.results)

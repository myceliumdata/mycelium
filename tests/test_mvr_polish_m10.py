"""Smoke tests: MVR redesign M10 — polish backlog (target-path gaps)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

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
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm-seeded"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


def _write_metering_network_json(
    path: Path,
    *,
    enabled: bool = True,
    default_funding_model: str = "caller_pays",
) -> None:
    data = json.loads((EXAMPLE_CRM / "network.json").read_text(encoding="utf-8"))
    metering = dict(data.get("metering") or {})
    metering["enabled"] = enabled
    metering["default_funding_model"] = default_funding_model
    metering["payment"] = {
        "enabled": False,
        "provider": "mock",
        "require_paid_before_accept": True,
    }
    data["metering"] = metering
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _mock_email_research(monkeypatch: pytest.MonkeyPatch) -> None:
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
        from agents.specialists.base import SpecialistStorage

        storage = SpecialistStorage(category=category)
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        for field in target_fields:
            rec[field] = versioned_found(
                at=now,
                value=f"{person_id[:8]}@polish.example",
                confidence=0.9,
                sources=[f"https://example.com/{person_id[:8]}"],
                category="contact",
                specialist_name="contact_specialist",
            )
        storage.save(data)
        return ResearchRunResult(fields_updated=list(target_fields), tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)


@pytest.fixture
def crm_target_env(
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
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
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
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
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
    reset_core_graph()
    return storage


@pytest.fixture
def crm_metering_target_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_entitlement_store()
    reset_quote_store()

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
    monkeypatch.setenv("MYCELIUM_ENTITLEMENTS_PATH", str(tmp_path / "entitlements.json"))
    monkeypatch.setenv("MYCELIUM_QUOTES_PATH", str(tmp_path / "quotes.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
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
    reset_core_graph()
    return storage


@pytest.mark.smoke
def test_step2_identity_only_deliver_with_provenance_scope(
    crm_target_env: CoreStorage,
) -> None:
    """P7 — provenance on step 1 without attrs; step 2 found omits provenance block."""
    _ = crm_target_env
    step1 = run_query(
        EntityQuery(lookup={"name": "Andrea Kalmans"}, provenance=True),
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None
    scope = get_delivery_store().get(step1.delivery.delivery_id)
    assert scope is not None
    assert scope.provenance is True
    assert not scope.requested_attributes

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert step2.provenance is None


@pytest.mark.smoke
def test_batch_step2_identity_only_found(
    crm_target_env: CoreStorage,
) -> None:
    """P19 — multi-match step 2 without attrs returns found + N identity rows."""
    _ = crm_target_env
    step1 = run_query(EntityQuery(lookup={"employer": "645 Ventures"}))
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 3
    assert step1.delivery is not None

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert len(step2.results) == 3
    assert all(row.get("name") for row in step2.results)


@pytest.mark.smoke
def test_target_principal_required_on_metered_quote(
    crm_metering_target_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P12 — sponsor_public funding blocks target step-1 quote without principal."""
    import os

    _ = crm_metering_target_env
    _write_metering_network_json(
        Path(os.environ["MYCELIUM_NETWORK_ROOT"]) / "network.json",
        enabled=True,
        default_funding_model="sponsor_public",
    )
    reset_core_graph()

    resp = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert resp.outcome == "principal_required"
    assert resp.quote is None
    assert "sponsor_public" in resp.message


@pytest.mark.smoke
def test_provenance_only_step1_quote_required(
    crm_metering_target_env: CoreStorage,
) -> None:
    """P13 — provenance-only step 1 on metered network issues quote_required."""
    _ = crm_metering_target_env
    resp = run_query(
        EntityQuery(lookup={"name": "Andrea Kalmans"}, provenance=True),
    )
    assert resp.outcome == "quote_required"
    assert resp.quote is not None
    assert resp.delivery is not None
    scope = get_delivery_store().get(resp.delivery.delivery_id)
    assert scope is not None
    assert scope.provenance is True
    assert not scope.requested_attributes


@pytest.mark.smoke
def test_metered_create_on_deliver_target_path(
    crm_metering_target_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P16 — metered create-on-deliver: quote then deliver assembles email."""
    _ = crm_metering_target_env
    _mock_email_research(monkeypatch)

    quoted = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert quoted.outcome == "quote_required"
    assert quoted.quote is not None
    assert quoted.delivery is not None

    delivered = run_query(
        EntityQuery(
            delivery_id=quoted.delivery.delivery_id,
            quote_id=str(quoted.quote["quote_id"]),
        ),
    )
    assert delivered.outcome == "assembled"
    assert len(delivered.results) == 1
    assert delivered.results[0].get("email") == delivered.results[0]["id"][:8] + "@polish.example"


@pytest.mark.smoke
def test_supervisor_no_legacy_entity_key_path(
    crm_target_env,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy entity_key fields are rejected at the model — no env flag path."""
    from graphs.core import run_query

    _ = crm_target_env
    with pytest.raises(ValidationError):
        EntityQuery(entity_key="Andrea Kalmans")  # type: ignore[call-arg]

    resp = run_query(
        EntityQuery(
            lookup={"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
        ),
    )
    assert resp.outcome == "lookup_resolved"

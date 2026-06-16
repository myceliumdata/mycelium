"""Smoke and unit tests for entity metering (Slice 10)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.metering_gate import (
    build_workload_spec,
    resolve_cache_state,
    should_meter,
)
from graphs.core import reset_core_graph
from graphs.core import run_query
from models.state import BillingPrincipal, EntityQuery, MyceliumGraphState
from network.entitlements import EntitlementRecord, get_entitlement_store, reset_entitlement_store
from network.metering_policy import MeteringPolicy, load_metering_policy
from network.paths import NetworkPaths
from network.quotes import (
    BuiltinQuoteProvider,
    WorkloadSpec,
    compute_scope_hash,
    get_quote_store,
    principal_required_error,
    reset_quote_store,
)
from storage.core import CoreStorage, get_storage, reset_storage
from network_helpers import copy_crm_network_manifest, import_seed_for_test, write_metering_network_json
from tools.research import ResearchRunResult
from versioned_storage_fixtures import versioned_found

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


def _load_default_metering_policy(tmp_path: Path) -> MeteringPolicy:
    """Load CRM metering policy from a tmp network root."""
    copy_crm_network_manifest(tmp_path)
    return load_metering_policy(paths=NetworkPaths.from_root(tmp_path))


def _write_metering_network_json(
    path: Path,
    *,
    enabled: bool = True,
    **overrides: Any,
) -> None:
    write_metering_network_json(path, enabled=enabled, **overrides)


def _mock_email_research(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

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
        calls.append(person_id)
        from agents.specialists.base import SpecialistStorage

        storage = SpecialistStorage(category=category)
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        for field in target_fields:
            rec[field] = versioned_found(
                at=now,
                value="paul.murphy@acme.example",
                confidence=0.9,
                sources=["https://example.com/paul"],
                category=category,
                specialist_name=specialist_name,
            )
        storage.save(data)
        return ResearchRunResult(fields_updated=list(target_fields), tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)
    return calls


@pytest.fixture
def crm_metering_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
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
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("MYCELIUM_AUTO_ACCEPT_QUOTES", raising=False)

    reset_category_tree()
    get_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    factory = get_agent_factory()
    factory.create_specialist(
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
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    reset_entitlement_store()
    reset_quote_store()


@pytest.mark.smoke
def test_load_metering_policy_disabled_when_explicit(tmp_path: Path) -> None:
    write_metering_network_json(tmp_path / "network.json", enabled=False)
    policy = load_metering_policy(paths=NetworkPaths.from_root(tmp_path))
    assert policy.enabled is False
    assert policy.meter_first_delivery is True


@pytest.mark.smoke
def test_scope_hash_changes_with_provenance() -> None:
    base = WorkloadSpec(entity_id="e1", requested_attributes=["email"])
    with_prov = base.model_copy(update={"provenance": True})
    assert compute_scope_hash(base) != compute_scope_hash(with_prov)


@pytest.mark.smoke
def test_builtin_quote_miss_includes_production_and_consumption(tmp_path: Path) -> None:
    policy = _load_default_metering_policy(tmp_path)
    workload = WorkloadSpec(
        entity_id="e1",
        requested_attributes=["email"],
        scope_hash="sha256:abc",
    )
    quote = BuiltinQuoteProvider().quote(
        workload=workload,
        cache_state="miss",
        funding_model="marginal",
        policy=policy,
        principal=None,
    )
    meters = {item.meter for item in quote.line_items}
    assert "research" in meters
    assert "query_value" in meters
    assert quote.total_usd == pytest.approx(2.05)


@pytest.mark.smoke
def test_builtin_quote_hit_marginal_consumption_only(tmp_path: Path) -> None:
    policy = _load_default_metering_policy(tmp_path)
    workload = WorkloadSpec(
        entity_id="e1",
        requested_attributes=["email"],
        scope_hash="sha256:abc",
    )
    quote = BuiltinQuoteProvider().quote(
        workload=workload,
        cache_state="hit",
        funding_model="marginal",
        policy=policy,
        principal=None,
    )
    assert len(quote.line_items) == 1
    assert quote.line_items[0].meter == "query_value"
    assert quote.avoidable_cost is not None


@pytest.mark.smoke
def test_entitlement_store_atomic_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "entitlements.json"
    monkeypatch.setenv("MYCELIUM_ENTITLEMENTS_PATH", str(path))
    reset_entitlement_store()
    store = get_entitlement_store()
    store.write(
        EntitlementRecord(
            entitlement_id="ent_test",
            scope_hash="sha256:test",
        ),
    )
    assert path.is_file()
    assert store.lookup_by_scope_hash("sha256:test") is not None


@pytest.mark.smoke
def test_quote_store_accept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "quotes.json"
    monkeypatch.setenv("MYCELIUM_QUOTES_PATH", str(path))
    reset_quote_store()
    policy = _load_default_metering_policy(tmp_path)
    workload = WorkloadSpec(entity_id="e1", requested_attributes=["email"], scope_hash="sha256:x")
    quote = BuiltinQuoteProvider().quote(
        workload=workload,
        cache_state="miss",
        funding_model="marginal",
        policy=policy,
        principal=None,
    )
    store = get_quote_store()
    store.issue(quote)
    accepted = store.accept(quote.quote_id)
    assert accepted is not None
    assert accepted.status == "accepted"


@pytest.mark.smoke
def test_principal_required_for_sponsor_public(tmp_path: Path) -> None:
    policy = _load_default_metering_policy(tmp_path)
    err = principal_required_error("sponsor_public", policy, None)
    assert err is not None
    err_ok = principal_required_error(
        "sponsor_public",
        policy,
        BillingPrincipal(kind="sponsor_id", id="s1"),
    )
    assert err_ok is None


@pytest.mark.smoke
def test_metering_disabled_no_quote(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_core_graph()
    reset_storage()
    reset_entity_registry()
    reset_entity_registry()
    reset_category_tree()
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    shutil.copy(SAMPLE_CATEGORIES, tmp_path / "categories.json")
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(tmp_path / "categories.json"))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    _mock_email_research(monkeypatch)
    import_seed_for_test(seed)
    reset_core_graph()
    registry = get_entity_registry()
    entity_ids = registry.lookup_by_target_lookup(
        {"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
    )
    assert len(entity_ids) == 1
    step1 = run_query(EntityQuery(id=entity_ids[0], requested_attributes=["email"]))
    assert step1.delivery is not None
    resp = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert resp.outcome == "assembled"
    assert resp.quote is None


@pytest.mark.smoke
def test_production_quote_then_accept(
    crm_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_metering_env
    _mock_email_research(monkeypatch)

    quoted = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert quoted.outcome == "quote_required"
    assert quoted.quote is not None
    assert quoted.quote["cache_state"] == "miss"
    meters = {item["meter"] for item in quoted.quote["line_items"]}
    assert "research" in meters
    assert "query_value" in meters
    quote_id = quoted.quote["quote_id"]
    assert quoted.delivery is not None

    accepted = run_query(
        EntityQuery(
            delivery_id=quoted.delivery.delivery_id,
            quote_id=quote_id,
        ),
    )
    assert accepted.outcome == "assembled"
    entitlements = json.loads(
        Path(__import__("os").environ["MYCELIUM_ENTITLEMENTS_PATH"]).read_text(),
    )
    assert entitlements.get("entitlements")
    quotes = json.loads(Path(__import__("os").environ["MYCELIUM_QUOTES_PATH"]).read_text())
    assert quotes["quotes"][quote_id]["status"] == "accepted"


@pytest.mark.smoke
def test_consumption_quote_cache_hit(
    crm_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_metering_env
    calls = _mock_email_research(monkeypatch)
    first = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    quote_id = first.quote["quote_id"]
    assert first.delivery is not None
    run_query(
        EntityQuery(
            delivery_id=first.delivery.delivery_id,
            quote_id=quote_id,
        ),
    )
    assert len(calls) == 1

    second = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert second.outcome == "quote_required"
    assert second.quote["cache_state"] == "hit"
    meters = {item["meter"] for item in second.quote["line_items"]}
    assert meters == {"query_value"}
    assert second.quote.get("avoidable_cost") is not None


@pytest.mark.smoke
def test_auto_accept_bypasses_gate(
    crm_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_metering_env
    _mock_email_research(monkeypatch)
    monkeypatch.setenv("MYCELIUM_AUTO_ACCEPT_QUOTES", "1")
    reset_core_graph()
    step1 = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None
    resp = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert resp.outcome == "assembled"
    assert step1.quote is None
    assert resp.quote is None


@pytest.mark.smoke
def test_invalid_quote_id_rejected(
    crm_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_metering_env
    _mock_email_research(monkeypatch)
    step1 = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert step1.outcome == "quote_required"
    assert step1.delivery is not None
    resp = run_query(
        EntityQuery(
            delivery_id=step1.delivery.delivery_id,
            quote_id="q_invalid",
        ),
    )
    assert resp.outcome == "quote_required"
    assert resp.quote["quote_id"] != "q_invalid"


@pytest.mark.smoke
def test_validation_still_free(
    crm_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_metering_env
    _mock_email_research(monkeypatch)
    resp = run_query(
        EntityQuery(lookup={"name": "Paul Murphy", "employer": "Acme Corp"}),
    )
    assert resp.outcome == "lookup_resolved"
    assert resp.delivery is not None
    assert resp.quote is None


@pytest.mark.smoke
def test_should_meter_skips_unknown() -> None:
    state = MyceliumGraphState(
        query=EntityQuery(lookup={"name": "X"}, requested_attributes=["email"]),
        entity_resolution_kind="unknown",
        validation_passed=False,
    )
    assert should_meter(state) is False


@pytest.mark.smoke
def test_resolve_cache_state_hit_from_entitlement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_ENTITLEMENTS_PATH", str(tmp_path / "entitlements.json"))
    reset_entitlement_store()
    workload = WorkloadSpec(
        entity_id="e1",
        requested_attributes=["email"],
        scope_hash="sha256:cached",
    )
    get_entitlement_store().write(
        EntitlementRecord(entitlement_id="ent1", scope_hash="sha256:cached"),
    )
    assert resolve_cache_state(workload, requested_attributes=["email"]) == "hit"


@pytest.mark.smoke
def test_build_workload_spec_from_state() -> None:
    state = MyceliumGraphState(
        query=EntityQuery(id="uuid-1", requested_attributes=["email"]),
        current_id="uuid-1",
    )
    spec = build_workload_spec(state)
    assert spec is not None
    assert spec.entity_id == "uuid-1"
    assert spec.requested_attributes == ["email"]


@pytest.mark.smoke
def test_provenance_meter_on_quote(tmp_path: Path) -> None:
    policy = _load_default_metering_policy(tmp_path)
    base = WorkloadSpec(entity_id="e1", requested_attributes=["email"], provenance=False)
    base = base.model_copy(update={"scope_hash": compute_scope_hash(base)})
    with_prov = base.model_copy(update={"provenance": True})
    with_prov = with_prov.model_copy(update={"scope_hash": compute_scope_hash(with_prov)})
    assert base.scope_hash != with_prov.scope_hash

    quote = BuiltinQuoteProvider().quote(
        workload=with_prov,
        cache_state="miss",
        funding_model="marginal",
        policy=policy,
        principal=None,
    )
    meters = {item.meter for item in quote.line_items}
    assert "query_provenance" in meters

    state = MyceliumGraphState(
        query=EntityQuery(
            id="uuid-prov",
            requested_attributes=["email"],
            provenance=True,
        ),
        current_id="uuid-prov",
    )
    spec = build_workload_spec(state)
    assert spec is not None
    assert spec.provenance is True


@pytest.mark.smoke
def test_full_duplicate_cache_hit_includes_production(
    crm_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    _ = crm_metering_env
    _mock_email_research(monkeypatch)
    network_path = Path(os.environ["MYCELIUM_NETWORK_ROOT"]) / "network.json"
    _write_metering_network_json(
        network_path,
        enabled=True,
        default_funding_model="full_duplicate",
    )
    reset_core_graph()
    first = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    quote_id = first.quote["quote_id"]
    assert first.delivery is not None
    run_query(
        EntityQuery(
            delivery_id=first.delivery.delivery_id,
            quote_id=quote_id,
        ),
    )

    second = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert second.outcome == "quote_required"
    assert second.quote["cache_state"] == "hit"
    kinds = {item["kind"] for item in second.quote["line_items"]}
    assert "production" in kinds


@pytest.mark.smoke
def test_meter_first_delivery_false_first_quote(
    crm_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    _ = crm_metering_env
    _mock_email_research(monkeypatch)
    network_path = Path(os.environ["MYCELIUM_NETWORK_ROOT"]) / "network.json"
    _write_metering_network_json(
        network_path,
        enabled=True,
        meter_first_delivery=False,
    )
    reset_core_graph()
    first = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert first.outcome == "quote_required"
    meters = {item["meter"] for item in first.quote["line_items"]}
    assert meters == {"research"}

    quote_id = first.quote["quote_id"]
    assert first.delivery is not None
    run_query(
        EntityQuery(
            delivery_id=first.delivery.delivery_id,
            quote_id=quote_id,
        ),
    )
    second = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert second.outcome == "quote_required"
    assert second.quote["cache_state"] == "hit"
    assert {item["meter"] for item in second.quote["line_items"]} == {"query_value"}


@pytest.mark.smoke
def test_sponsor_public_principal_required_e2e(
    crm_metering_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    _ = crm_metering_env
    _mock_email_research(monkeypatch)
    network_path = Path(os.environ["MYCELIUM_NETWORK_ROOT"]) / "network.json"
    _write_metering_network_json(
        network_path,
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

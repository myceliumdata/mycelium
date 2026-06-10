"""Smoke and unit tests for entity payment settlement (Slice 11)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
from agents.registry import reset_agent_registry
from agents.seed import reset_seed_data
from graphs.core import reset_core_graph, run_query
from models.state import BillingPrincipal, EntityQuery
from network.credits import get_credit_store, reset_credit_store
from network.entitlements import reset_entitlement_store
from network.metering_policy import load_metering_policy
from network.payment import PaymentError, settle_quote
from network.quotes import get_quote_store, reset_quote_store
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
        from datetime import datetime, timezone

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


def _write_payment_network_json(
    path: Path,
    *,
    metering_enabled: bool = True,
    payment_enabled: bool = True,
    provider: str = "mock",
    **overrides: Any,
) -> None:
    payment = {
        "enabled": payment_enabled,
        "provider": provider,
        "require_paid_before_accept": True,
    }
    payment.update(overrides.pop("payment", {}) or {})
    _write_metering_network_json(
        path,
        enabled=metering_enabled,
        payment=payment,
        **overrides,
    )


@pytest.fixture
def crm_payment_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_seed_data()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_entitlement_store()
    reset_quote_store()
    reset_credit_store()

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    _write_payment_network_json(tmp_path / "network.json")

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
    monkeypatch.setenv("MYCELIUM_CREDITS_PATH", str(tmp_path / "credits.json"))
    monkeypatch.setenv("MYCELIUM_METER_RESEARCH_USD", "2.0")
    monkeypatch.setenv("MYCELIUM_METER_QUERY_VALUE_USD", "0.05")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("MYCELIUM_AUTO_ACCEPT_QUOTES", raising=False)
    monkeypatch.delenv("MYCELIUM_AUTO_SETTLE_QUOTES", raising=False)

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
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    reset_entitlement_store()
    reset_quote_store()
    reset_credit_store()


def _bind_and_quote(
    *,
    payment_enabled: bool = True,
) -> tuple[str, dict[str, Any]]:
    run_query(EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"}))
    quoted = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert quoted.outcome == "quote_required"
    assert quoted.quote is not None
    return quoted.quote["quote_id"], quoted.quote


@pytest.mark.smoke
def test_payment_disabled_quote_id_without_pay(
    crm_payment_env: CoreStorage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _write_payment_network_json(
        tmp_path / "network.json",
        payment_enabled=False,
    )
    _mock_email_research(monkeypatch)
    reset_core_graph()

    quote_id, _ = _bind_and_quote()
    resp = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
            quote_id=quote_id,
        ),
    )
    assert resp.outcome == "assembled"


@pytest.mark.smoke
def test_mock_settle_then_accept(
    crm_payment_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _mock_email_research(monkeypatch)

    quote_id, _ = _bind_and_quote()
    receipt = settle_quote(quote_id, proof="test:ok")
    assert receipt.provider == "mock"

    resp = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
            quote_id=quote_id,
        ),
    )
    assert resp.outcome == "assembled"
    quotes = json.loads(Path(__import__("os").environ["MYCELIUM_QUOTES_PATH"]).read_text())
    assert quotes["quotes"][quote_id]["status"] == "accepted"


@pytest.mark.smoke
def test_payment_required_before_settle(
    crm_payment_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _mock_email_research(monkeypatch)

    quote_id, quote = _bind_and_quote()
    blocked = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
            quote_id=quote_id,
        ),
    )
    assert blocked.outcome == "payment_required"
    assert blocked.quote is not None
    assert blocked.quote["quote_id"] == quote_id
    assert blocked.quote.get("total_usd") == quote.get("total_usd")


@pytest.mark.smoke
def test_credit_insufficient(
    crm_payment_env: CoreStorage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _write_payment_network_json(
        tmp_path / "network.json",
        provider="credit",
    )
    reset_core_graph()
    _mock_email_research(monkeypatch)

    quote_id, _ = _bind_and_quote()
    with pytest.raises(PaymentError, match="insufficient credits"):
        settle_quote(
            quote_id,
            principal=BillingPrincipal(kind="tenant", id="acme"),
        )


@pytest.mark.smoke
def test_credit_success(
    crm_payment_env: CoreStorage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _write_payment_network_json(
        tmp_path / "network.json",
        provider="credit",
    )
    reset_core_graph()
    _mock_email_research(monkeypatch)

    get_credit_store().set_balance("acme", 10.0)
    quote_id, quote = _bind_and_quote()
    receipt = settle_quote(
        quote_id,
        principal=BillingPrincipal(kind="tenant", id="acme"),
    )
    assert receipt.provider == "credit"
    assert get_credit_store().get_balance("acme") == pytest.approx(
        10.0 - quote["total_usd"],
    )

    resp = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
            quote_id=quote_id,
        ),
    )
    assert resp.outcome == "assembled"


@pytest.mark.smoke
def test_x402_stub_proof(
    crm_payment_env: CoreStorage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _write_payment_network_json(
        tmp_path / "network.json",
        provider="x402_stub",
    )
    reset_core_graph()

    quote_id, _ = _bind_and_quote()
    with pytest.raises(PaymentError, match="x402:test:"):
        settle_quote(quote_id, proof="bad")

    receipt = settle_quote(quote_id, proof="x402:test:abc")
    assert receipt.provider == "x402_stub"
    stored = get_quote_store().get(quote_id)
    assert stored is not None
    assert stored.payment_proof == "x402:test:abc"


@pytest.mark.smoke
def test_auto_settle_bypass(
    crm_payment_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _mock_email_research(monkeypatch)
    monkeypatch.setenv("MYCELIUM_AUTO_SETTLE_QUOTES", "1")
    reset_core_graph()

    quote_id, _ = _bind_and_quote()
    resp = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
            quote_id=quote_id,
        ),
    )
    assert resp.outcome == "assembled"
    stored = get_quote_store().get(quote_id)
    assert stored is not None
    assert stored.status == "accepted"


@pytest.mark.smoke
def test_load_metering_policy_parses_payment(tmp_path: Path) -> None:
    network = tmp_path / "network.json"
    network.write_text(
        json.dumps(
            {
                "metering": {
                    "enabled": True,
                    "payment": {"enabled": True, "provider": "credit"},
                },
            },
        ),
        encoding="utf-8",
    )
    policy = load_metering_policy(
        paths=__import__("network.paths").NetworkPaths.from_root(tmp_path),
    )
    assert policy.payment.enabled is True
    assert policy.payment.provider == "credit"


def _expire_quote_in_store(quote_id: str) -> None:
    store = get_quote_store()
    quote = store.get(quote_id)
    assert quote is not None
    expired = quote.model_copy(update={"expires_at": "2000-01-01T00:00:00+00:00"})
    store._data.quotes[quote_id] = expired
    store._save()


@pytest.mark.smoke
def test_settle_quote_rejects_expired(
    crm_payment_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _mock_email_research(monkeypatch)

    quote_id, _ = _bind_and_quote()
    _expire_quote_in_store(quote_id)

    with pytest.raises(PaymentError, match="expired"):
        settle_quote(quote_id, proof="test:ok")


@pytest.mark.smoke
def test_credit_deduct_after_mark_paid(
    crm_payment_env: CoreStorage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _write_payment_network_json(
        tmp_path / "network.json",
        provider="credit",
    )
    reset_core_graph()

    get_credit_store().set_balance("acme", 10.0)
    quote_id, _ = _bind_and_quote()

    def _fail_mark_paid(self, *args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr("network.quotes.QuoteStore.mark_paid", _fail_mark_paid)

    with pytest.raises(PaymentError, match="failed to mark quote paid"):
        settle_quote(
            quote_id,
            principal=BillingPrincipal(kind="tenant", id="acme"),
            provider_name="credit",
        )
    assert get_credit_store().get_balance("acme") == pytest.approx(10.0)


@pytest.mark.smoke
def test_mcp_pay_quote_round_trip(
    crm_payment_env: CoreStorage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _mock_email_research(monkeypatch)

    from network.paths import NetworkPaths, apply_network_paths

    apply_network_paths(NetworkPaths.from_root(tmp_path))

    quote_id, _ = _bind_and_quote()

    from mycelium_mcp.server import pay_quote, query_entity

    pay_raw = pay_quote(json.dumps({"quote_id": quote_id, "proof": "test:mcp"}))
    pay_payload = json.loads(pay_raw)
    assert pay_payload["status"] == "paid"
    assert pay_payload["receipt"]["quote_id"] == quote_id

    query_raw = query_entity(
        json.dumps(
            {
                "entity_key": "Paul Murphy",
                "binding": {"employer": "Acme Corp"},
                "requested_attributes": ["email"],
                "quote_id": quote_id,
            },
        ),
    )
    query_payload = json.loads(query_raw)
    assert query_payload["outcome"] == "assembled"


@pytest.mark.smoke
def test_accept_rejects_expired_paid_quote(
    crm_payment_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_payment_env
    _mock_email_research(monkeypatch)

    quote_id, _ = _bind_and_quote()
    settle_quote(quote_id, proof="test:ok")
    _expire_quote_in_store(quote_id)

    resp = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
            quote_id=quote_id,
        ),
    )
    assert resp.outcome != "assembled"
    assert resp.outcome == "quote_required"
    assert resp.quote is not None
    assert resp.quote["quote_id"] != quote_id

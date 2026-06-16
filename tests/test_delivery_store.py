"""Unit tests for DeliveryStore and quote TTL (MVR redesign slice M2)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from network.delivery import (
    DeliveryScope,
    delivery_is_expired,
    delivery_ttl_seconds,
    get_delivery_store,
    issue_delivery,
    reset_delivery_store,
)
from network.metering_policy import load_metering_policy
from network.paths import NetworkPaths
from network.quotes import BuiltinQuoteProvider, WorkloadSpec, quote_ttl_seconds
from network_helpers import write_metering_network_json


@pytest.fixture(autouse=True)
def _reset_delivery_store() -> None:
    reset_delivery_store()
    yield
    reset_delivery_store()


@pytest.mark.smoke
def test_issue_delivery_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(tmp_path / "deliveries.json"))
    scope = issue_delivery(
        entity_ids=["ent-1", "ent-2"],
        lookup={"employer": "IBM"},
        requested_attributes=["linkedin"],
        provenance=True,
    )
    assert scope.delivery_id.startswith("d_")
    assert scope.entity_ids == ["ent-1", "ent-2"]
    assert scope.lookup == {"employer": "IBM"}
    assert scope.requested_attributes == ["linkedin"]
    assert scope.provenance is True

    store = get_delivery_store()
    store.put(scope)
    loaded = store.get(scope.delivery_id)
    assert loaded is not None
    assert loaded.model_dump() == scope.model_dump()
    assert (tmp_path / "deliveries.json").is_file()


@pytest.mark.smoke
def test_delivery_get_returns_none_when_expired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(tmp_path / "deliveries.json"))
    now = datetime(2026, 6, 13, 10, 0, 0, tzinfo=timezone.utc)
    scope = issue_delivery(
        entity_ids=["ent-1"],
        lookup={"name": "Jane"},
        now=now,
    )
    store = get_delivery_store()
    store.put(scope)
    later = now + timedelta(seconds=delivery_ttl_seconds() + 1)
    assert store.get(scope.delivery_id, now=later) is None
    assert store.is_expired(scope.delivery_id, now=later)


@pytest.mark.smoke
def test_delivery_get_returns_none_for_unknown_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(tmp_path / "deliveries.json"))
    store = get_delivery_store()
    assert store.get("d_missing") is None
    assert store.is_expired("d_missing")


@pytest.mark.smoke
def test_delivery_is_expired_helper() -> None:
    scope = DeliveryScope(
        delivery_id="d_test",
        expires_at="2000-01-01T00:00:00+00:00",
        entity_ids=["ent-1"],
    )
    assert delivery_is_expired(scope)


@pytest.mark.smoke
def test_quote_ttl_defaults_to_five_minutes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MYCELIUM_QUOTE_TTL_SEC", raising=False)
    assert quote_ttl_seconds() == 300
    write_metering_network_json(tmp_path / "network.json", enabled=True)
    policy = load_metering_policy(paths=NetworkPaths.from_root(tmp_path))
    quote = BuiltinQuoteProvider().quote(
        workload=WorkloadSpec(entity_id="e1", requested_attributes=["email"], scope_hash="sha256:x"),
        cache_state="miss",
        funding_model="marginal",
        policy=policy,
        principal=None,
    )
    expires = datetime.fromisoformat(quote.expires_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = (expires - now).total_seconds()
    assert 250 <= delta <= 310

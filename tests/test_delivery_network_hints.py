"""Smoke tests for CLI delivery_id network hints."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from network.delivery import DeliveryScope
from network.delivery_hints import (
    delivery_not_found_message,
    find_delivery_on_other_network,
    format_step2_cli_hint,
)
from network.registry import NetworkEntry

_MINIMAL_NETWORK_JSON = {
    "name": "test-net",
    "mvr": {
        "default_record_type": "person",
        "record_types": {
            "person": {
                "bind_fields": ["name"],
                "new_records": "query_allowed",
            },
        },
    },
}


def _write_network_root(root: Path, *, name: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = dict(_MINIMAL_NETWORK_JSON)
    payload["name"] = name
    (root / "network.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_delivery(
    root: Path,
    delivery_id: str,
    *,
    expires_at: str,
) -> None:
    scope = DeliveryScope(
        delivery_id=delivery_id,
        expires_at=expires_at,
        entity_ids=["ent-1"],
        lookup={"name": "Test"},
    )
    payload = {
        "version": "1.0",
        "deliveries": {delivery_id: scope.model_dump()},
    }
    (root / "deliveries.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


@pytest.mark.smoke
def test_find_delivery_on_other_network(tmp_path: Path) -> None:
    crm_root = tmp_path / "crm"
    baseball_root = tmp_path / "baseball"
    _write_network_root(crm_root, name="crm")
    _write_network_root(baseball_root, name="baseball")

    delivery_id = "d_testother01"
    future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    _write_delivery(baseball_root, delivery_id, expires_at=future)

    registry = [
        NetworkEntry(name="crm", root=str(crm_root)),
        NetworkEntry(name="baseball", root=str(baseball_root), default=True),
    ]

    found = find_delivery_on_other_network(
        delivery_id,
        active_root=crm_root,
        registry=registry,
    )
    assert found is not None
    assert found.name == "baseball"

    message = delivery_not_found_message(
        delivery_id,
        active_root=crm_root,
        registry=registry,
    )
    assert "on network 'crm'" in message
    assert "issued on network 'baseball'" in message
    assert "--network baseball" in message
    assert delivery_id in message


@pytest.mark.smoke
def test_expired_on_active_network(tmp_path: Path) -> None:
    root = tmp_path / "crm"
    _write_network_root(root, name="crm")

    delivery_id = "d_expired01"
    past = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    _write_delivery(root, delivery_id, expires_at=past)

    registry = [NetworkEntry(name="crm", root=str(root), default=True)]

    message = delivery_not_found_message(
        delivery_id,
        active_root=root,
        registry=registry,
    )
    assert "expired" in message.lower()
    assert "crm" in message
    assert "issued on network" not in message


@pytest.mark.smoke
def test_unknown_delivery_fallback(tmp_path: Path) -> None:
    root = tmp_path / "crm"
    _write_network_root(root, name="crm")
    registry = [NetworkEntry(name="crm", root=str(root), default=True)]

    message = delivery_not_found_message(
        "d_missing01",
        active_root=root,
        registry=registry,
    )
    assert "d_missing01" in message
    assert "Re-run step 1" in message
    assert "--network <name>" in message


@pytest.mark.smoke
def test_step1_hint_includes_network_name() -> None:
    hint = format_step2_cli_hint(
        delivery_id="d_abc123",
        network_name="baseball",
        network_root=Path("/tmp/baseball"),
    )
    assert hint.startswith("Step 2 (same network):")
    assert "--network baseball" in hint
    assert "--delivery-id d_abc123" in hint
    assert "--network-dir" not in hint


@pytest.mark.smoke
def test_step1_hint_uses_network_dir_when_no_name(tmp_path: Path) -> None:
    root = tmp_path / "custom-root"
    hint = format_step2_cli_hint(
        delivery_id="d_abc123",
        network_name=None,
        network_root=root,
        quote_id="q_xyz",
    )
    assert f"--network-dir {root.resolve()}" in hint
    assert "--quote-id q_xyz" in hint

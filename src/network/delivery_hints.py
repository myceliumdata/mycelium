"""Human-facing CLI hints for delivery_id network mismatches and expiry."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from network.delivery import DeliveryScope, delivery_is_expired
from network.paths import network_metadata
from network.registry import NetworkEntry, load_network_registry, network_root_status

DeliveryState = Literal["missing", "expired", "active"]


def _delivery_state_on_root(
    delivery_id: str,
    root: Path,
    *,
    now: datetime | None = None,
) -> DeliveryState:
    path = root / "deliveries.json"
    if not path.is_file():
        return "missing"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "missing"
    if not isinstance(raw, dict):
        return "missing"
    deliveries = raw.get("deliveries")
    if not isinstance(deliveries, dict):
        return "missing"
    scope_raw = deliveries.get(delivery_id)
    if scope_raw is None:
        return "missing"
    try:
        scope = DeliveryScope.model_validate(scope_raw)
    except Exception:
        return "missing"
    if delivery_is_expired(scope, now=now):
        return "expired"
    return "active"


def _network_label(*, network_name: str | None, network_root: Path) -> str:
    if network_name and network_name.strip():
        return network_name.strip()
    return str(network_root.expanduser().resolve())


def _network_selector(*, network_name: str | None, network_root: Path) -> str:
    if network_name and network_name.strip():
        return f"--network {network_name.strip()}"
    return f"--network-dir {network_root.expanduser().resolve()}"


def find_delivery_on_other_network(
    delivery_id: str,
    *,
    active_root: Path,
    registry: list[NetworkEntry] | None = None,
    now: datetime | None = None,
) -> NetworkEntry | None:
    """Return the single other registered network with a non-expired delivery, if any."""
    resolved_active = active_root.expanduser().resolve()
    matches: list[NetworkEntry] = []
    for entry in registry or load_network_registry():
        root = Path(entry.root).expanduser().resolve()
        if root == resolved_active:
            continue
        if network_root_status(root) != "ok":
            continue
        if _delivery_state_on_root(delivery_id, root, now=now) == "active":
            matches.append(entry)
    if len(matches) == 1:
        return matches[0]
    return None


def delivery_not_found_message(
    delivery_id: str,
    *,
    active_root: Path,
    registry: list[NetworkEntry] | None = None,
    now: datetime | None = None,
) -> str:
    """Build a specific human message for step-2 deliver misses."""
    resolved_active = active_root.expanduser().resolve()
    meta = network_metadata(root=resolved_active)
    active_name = meta.get("network_name")
    active_label = _network_label(network_name=active_name, network_root=resolved_active)

    state = _delivery_state_on_root(delivery_id, resolved_active, now=now)
    if state == "expired":
        return (
            f"Delivery {delivery_id!r} expired on network {active_label!r}. "
            f"Re-run step 1 on the same network."
        )

    other = find_delivery_on_other_network(
        delivery_id,
        active_root=resolved_active,
        registry=registry,
        now=now,
    )
    if other is not None:
        other_root = Path(other.root).expanduser().resolve()
        retry = _network_selector(network_name=other.name, network_root=other_root)
        return (
            f"No valid delivery for {delivery_id!r} on network {active_label!r}.\n"
            f"This delivery_id was issued on network {other.name!r}.\n"
            f"Retry: uv run mycelium query {retry} --delivery-id {delivery_id}"
        )

    return (
        f"No valid delivery for {delivery_id!r} on network {active_label!r}. "
        "Re-run step 1 on the same network, then step 2 with --network <name>."
    )


def format_step2_cli_hint(
    *,
    delivery_id: str,
    network_name: str | None = None,
    network_root: Path | None = None,
    quote_id: str | None = None,
) -> str:
    """stderr copy-paste hint after step-1 lookup_resolved or quote_required."""
    if network_root is None and not (network_name and network_name.strip()):
        raise ValueError("network_name or network_root required for step-2 hint")
    root = network_root.expanduser().resolve() if network_root is not None else Path(".")
    selector = _network_selector(network_name=network_name, network_root=root)
    parts = ["uv run mycelium query", selector, f"--delivery-id {delivery_id}"]
    if quote_id and str(quote_id).strip():
        parts.append(f"--quote-id {quote_id.strip()}")
    return "Step 2 (same network): " + " ".join(parts)

"""Delivery scope issuance and store (MVR redesign slice M2)."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

from network.paths import runtime_path


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def delivery_ttl_seconds() -> int:
    return _env_int("MYCELIUM_DELIVERY_TTL_SEC", 300)


class DeliveryScope(BaseModel):
    delivery_id: str
    expires_at: str
    entity_ids: list[str] = Field(default_factory=list)
    lookup: dict[str, Any] = Field(default_factory=dict)
    requested_attributes: list[str] = Field(default_factory=list)
    provenance: bool = False
    create_on_deliver: bool = Field(
        default=False,
        description="Step-2 should bind a provisional registry row from lookup (0 step-1 matches).",
    )


class DeliveriesDocument(BaseModel):
    version: str = "1.0"
    deliveries: dict[str, DeliveryScope] = Field(default_factory=dict)


_delivery_store: "DeliveryStore | None" = None


def reset_delivery_store() -> None:
    global _delivery_store
    _delivery_store = None


def delivery_is_expired(scope: DeliveryScope, *, now: datetime | None = None) -> bool:
    """Return True when ``scope.expires_at`` is in the past (or unparseable)."""
    try:
        expires = datetime.fromisoformat(scope.expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current >= expires


def issue_delivery(
    *,
    entity_ids: list[str],
    lookup: dict[str, Any] | None = None,
    requested_attributes: list[str] | None = None,
    provenance: bool = False,
    create_on_deliver: bool = False,
    now: datetime | None = None,
) -> DeliveryScope:
    """Create a new delivery scope with ``d_`` id and configured TTL."""
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return DeliveryScope(
        delivery_id=f"d_{uuid.uuid4().hex[:12]}",
        expires_at=(current + timedelta(seconds=delivery_ttl_seconds())).isoformat(),
        entity_ids=list(entity_ids),
        lookup=dict(lookup or {}),
        requested_attributes=list(requested_attributes or []),
        provenance=bool(provenance),
        create_on_deliver=bool(create_on_deliver),
    )


class DeliveryStore:
    """Atomic JSON store for issued delivery scopes."""

    def __init__(self, path: str | None = None) -> None:
        self.path = (
            runtime_path("MYCELIUM_DELIVERIES_PATH")
            if path is None
            else __import__("pathlib").Path(path)
        )
        self._data = DeliveriesDocument()
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(raw, dict):
            self._data = DeliveriesDocument.model_validate(raw)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._data.model_dump_json(indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=self.path.parent, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_path, self.path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def put(self, scope: DeliveryScope) -> DeliveryScope:
        self._data.deliveries[scope.delivery_id] = scope
        self._save()
        return scope

    def get(self, delivery_id: str, *, now: datetime | None = None) -> DeliveryScope | None:
        scope = self._data.deliveries.get(delivery_id)
        if scope is None:
            return None
        if delivery_is_expired(scope, now=now):
            return None
        return scope

    def is_expired(self, delivery_id: str, *, now: datetime | None = None) -> bool:
        scope = self._data.deliveries.get(delivery_id)
        if scope is None:
            return True
        return delivery_is_expired(scope, now=now)

    def all_deliveries(self) -> dict[str, DeliveryScope]:
        return dict(self._data.deliveries)


def get_delivery_store() -> DeliveryStore:
    global _delivery_store
    if _delivery_store is None:
        _delivery_store = DeliveryStore()
    return _delivery_store

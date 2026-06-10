"""Entitlement store for workload scope hashes (Slice 10)."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from network.paths import runtime_path


class EntitlementRecord(BaseModel):
    entitlement_id: str
    scope_hash: str
    sponsor_id: str | None = None
    visibility: str = "public"
    period_seconds: int | None = None
    expires_at: str | None = None
    funded_line_items: list[str] = Field(default_factory=list)
    created_at: str = ""


class EntitlementsDocument(BaseModel):
    version: str = "1.0"
    entitlements: dict[str, EntitlementRecord] = Field(default_factory=dict)


_entitlement_store: "EntitlementStore | None" = None


def reset_entitlement_store() -> None:
    global _entitlement_store
    _entitlement_store = None


class EntitlementStore:
    """Atomic JSON store keyed by entitlement_id; lookup by scope_hash."""

    def __init__(self, path: str | None = None) -> None:
        self.path = (
            runtime_path("MYCELIUM_ENTITLEMENTS_PATH")
            if path is None
            else __import__("pathlib").Path(path)
        )
        self._data = EntitlementsDocument()
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(raw, dict):
            self._data = EntitlementsDocument.model_validate(raw)

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

    def lookup_by_scope_hash(self, scope_hash: str) -> EntitlementRecord | None:
        for record in self._data.entitlements.values():
            if record.scope_hash == scope_hash and not self._is_expired(record):
                return record
        return None

    def write(self, record: EntitlementRecord) -> None:
        if not record.created_at:
            record = record.model_copy(
                update={"created_at": datetime.now(timezone.utc).isoformat()},
            )
        self._data.entitlements[record.entitlement_id] = record
        self._save()

    def all_records(self) -> dict[str, EntitlementRecord]:
        return dict(self._data.entitlements)

    @staticmethod
    def _is_expired(record: EntitlementRecord) -> bool:
        if not record.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(record.expires_at.replace("Z", "+00:00"))
        except ValueError:
            return False
        now = datetime.now(timezone.utc)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now >= expires


def get_entitlement_store() -> EntitlementStore:
    global _entitlement_store
    if _entitlement_store is None:
        _entitlement_store = EntitlementStore()
    return _entitlement_store

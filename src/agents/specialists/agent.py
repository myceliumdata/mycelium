"""Specialist agent base class — autonomous storage owner with overridable I/O."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Callable

from agents.specialists.base import SpecialistStorage
from agents.specialists.computed import append_computed_version, build_computed_version_body
from agents.specialists.fields import (
    append_version,
    current_status,
    current_value,
    current_value_matches,
    field_is_na,
    is_versioned_field,
)
from agents.specialists.snapshots import (
    entity_field_status_row,
    field_context_snapshot,
    field_snapshot,
)


def _actor_body(*, kind: str, category: str, specialist: str) -> dict[str, str]:
    return {"kind": kind, "category": category, "specialist": specialist}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SpecialistAgent:
    """Framework default specialist agent; subclass to override storage or research."""

    category: str = ""
    agent_name: str = ""

    def __init__(
        self,
        *,
        category: str | None = None,
        agent_name: str | None = None,
        storage: SpecialistStorage | None = None,
    ) -> None:
        resolved_category = category or self.category
        if not resolved_category:
            raise ValueError("SpecialistAgent requires category")
        self.category = resolved_category
        self.agent_name = agent_name or self.agent_name or f"{resolved_category}_specialist"
        self._storage = storage
        self._storage_key: tuple[str, str] | None = None

    def _resolve_storage(self) -> SpecialistStorage:
        if self._storage is not None and self._storage_key is None:
            return self._storage
        from network.paths import runtime_path

        base_dir = runtime_path("MYCELIUM_AGENT_DATA_DIR")
        key = (str(base_dir.expanduser().resolve()), self.category)
        if self._storage is None or self._storage_key != key:
            self._storage = SpecialistStorage(category=self.category, base_dir=base_dir)
            self._storage_key = key
        return self._storage

    @property
    def storage(self) -> SpecialistStorage:
        return self._resolve_storage()

    def optimize_storage_threshold(self) -> int:
        """Records-at-or-above this count trigger migration (env override)."""
        raw = os.getenv("MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD", "50")
        try:
            return int(raw)
        except ValueError:
            return 50

    def optimize_storage(self) -> bool:
        """Return True when record count crosses threshold on versioned JSON storage."""
        if self.storage.current_strategy() != "versioned_provenance_v1":
            return False
        return self.record_count() >= self.optimize_storage_threshold()

    def migrate_to(self, target: str) -> None:
        """Delegate storage strategy migration to the backing store."""
        self.storage.migrate_to(target)

    def _maybe_optimize_storage(self) -> None:
        if not self.optimize_storage():
            return
        try:
            self.migrate_to("minisql_v1")
        except NotImplementedError:
            pass

    def record_count(self) -> int:
        records = self.storage.load().get("records", {})
        if not isinstance(records, dict):
            return 0
        return len(records)

    def write_fields(
        self,
        entity_id: str,
        fields: dict[str, str],
        *,
        actor_kind: str,
        at: str | None = None,
    ) -> dict[str, str]:
        """Write fields to specialist storage; return current values for written keys."""
        self._maybe_optimize_storage()
        timestamp = at or _now_iso()
        use_incremental = self.storage.current_strategy() == "minisql_v1"
        if use_incremental:
            record = self.storage.load_entity(entity_id)
            if record is None:
                record = {}
        else:
            data = self.storage.load()
            records = data.setdefault("records", {})
            record = records.setdefault(entity_id, {})
        current: dict[str, str] = {}
        for field, value in fields.items():
            key = field.strip().lower()
            if not key or not str(value).strip():
                continue
            if current_value_matches(record.get(key), str(value)):
                existing = current_value(record.get(key))
                if existing is not None:
                    current[key] = existing
                continue
            version_body: dict[str, Any] = {
                "at": timestamp,
                "status": "found",
                "value": str(value).strip(),
                "actor": _actor_body(
                    kind=actor_kind,
                    category=self.category,
                    specialist=self.agent_name,
                ),
            }
            record[key] = append_version(record.get(key), version_body)
            written = current_value(record[key])
            if written is not None:
                current[key] = written
        if use_incremental:
            self.storage.save_entity(entity_id, record)
        else:
            self.storage.save(data)
        return current

    def write_computed_field(
        self,
        entity_id: str,
        field: str,
        *,
        value: str,
        sources: list[dict[str, Any]],
        computation: dict[str, str],
        parameters: dict[str, str],
        at: str | None = None,
    ) -> str:
        """Write a computed field version with dataset/computation provenance."""
        self._maybe_optimize_storage()
        timestamp = at or _now_iso()
        key = field.strip().lower()
        if not key:
            return ""
        use_incremental = self.storage.current_strategy() == "minisql_v1"
        if use_incremental:
            record = self.storage.load_entity(entity_id)
            if record is None:
                record = {}
        else:
            data = self.storage.load()
            records = data.setdefault("records", {})
            record = records.setdefault(entity_id, {})
        if current_value_matches(record.get(key), str(value)):
            existing = current_value(record.get(key))
            if existing is not None:
                return existing
        version_body = build_computed_version_body(
            value=str(value).strip(),
            actor=_actor_body(
                kind="specialist",
                category=self.category,
                specialist=self.agent_name,
            ),
            sources=sources,
            computation=computation,
            parameters=parameters,
            at=timestamp,
        )
        record[key] = append_computed_version(record.get(key), version_body)
        written = current_value(record[key])
        if use_incremental:
            self.storage.save_entity(entity_id, record)
        else:
            self.storage.save(data)
        return written or str(value).strip()

    def write_na_field(
        self,
        entity_id: str,
        field: str,
        *,
        at: str | None = None,
        actor_kind: str = "specialist",
    ) -> None:
        """Write an ``na`` status version for a field when compute is unavailable."""
        key = field.strip().lower()
        if not key:
            return
        timestamp = at or _now_iso()
        use_incremental = self.storage.current_strategy() == "minisql_v1"
        if use_incremental:
            record = self.storage.load_entity(entity_id)
            if record is None:
                record = {}
        else:
            data = self.storage.load()
            records = data.setdefault("records", {})
            record = records.setdefault(entity_id, {})
        if field_is_na(record.get(key)):
            return
        version_body: dict[str, Any] = {
            "at": timestamp,
            "status": "na",
            "actor": _actor_body(
                kind=actor_kind,
                category=self.category,
                specialist=self.agent_name,
            ),
        }
        record[key] = append_version(record.get(key), version_body)
        if use_incremental:
            self.storage.save_entity(entity_id, record)
        else:
            self.storage.save(data)

    def read_fields(
        self,
        entity_id: str,
        fields: list[str],
        *,
        include_versions: bool = False,
        include_provenance: bool | None = None,
    ) -> dict[str, Any]:
        with_provenance = include_versions if include_provenance is None else include_provenance
        if self.storage.current_strategy() == "minisql_v1":
            record = self.storage.load_entity(entity_id)
            if record is None:
                record = {}
        else:
            record = self.storage.load().get("records", {}).get(entity_id, {})
            if not isinstance(record, dict):
                record = {}
        out: dict[str, Any] = {}
        for raw_field in fields:
            field = raw_field.strip().lower()
            if not field:
                continue
            entry = record.get(field)
            out[field] = field_snapshot(
                entry,
                field_name=field,
                category=self.category,
                include_provenance=with_provenance,
            )
        return out

    def bootstrap_entity(
        self,
        entity_id: str,
        fields: dict[str, str],
        *,
        actor_kind: str = "seed_bootstrap",
    ) -> dict[str, str]:
        return self.write_fields(
            entity_id,
            fields,
            actor_kind=actor_kind,
        )

    def analyze_storage(self) -> dict[str, Any]:
        strategy_name = self.storage.current_strategy()
        payload = self.storage.load()
        records = payload.get("records", {}) if isinstance(payload, dict) else {}
        if not isinstance(records, dict):
            records = {}
        fields_tracked: set[str] = set()
        pending = found = na = 0
        for record in records.values():
            if not isinstance(record, dict):
                continue
            for field_name, value in record.items():
                fields_tracked.add(field_name)
                if not isinstance(value, dict) or not is_versioned_field(value):
                    continue
                status = current_status(value)
                if status == "pending":
                    pending += 1
                elif status == "found":
                    found += 1
                elif status == "na":
                    na += 1
        return {
            "storage_strategy": strategy_name,
            "record_count": len(records),
            "fields_tracked": sorted(fields_tracked),
            "pending_count": pending,
            "na_count": na,
            "found_count": found,
        }

    def read_category_slice(
        self,
        entity_ids: list[str],
        *,
        bind_fields: frozenset[str] | set[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        records = self.storage.load().get("records", {})
        if not isinstance(records, dict):
            return {}
        skip = bind_fields or frozenset()
        out: dict[str, dict[str, Any]] = {}
        for entity_id in entity_ids:
            row = records.get(entity_id)
            if not isinstance(row, dict):
                continue
            entity_slice: dict[str, Any] = {}
            for field_name, entry in row.items():
                if field_name in skip:
                    continue
                entity_slice[field_name] = field_context_snapshot(
                    entry,
                    field_name=field_name,
                    category=self.category,
                )
            if entity_slice:
                out[entity_id] = entity_slice
        return out

    def entity_field_statuses(self, entity_id: str) -> list[dict[str, Any]]:
        record = self.storage.load().get("records", {}).get(entity_id, {})
        if not isinstance(record, dict):
            return []
        rows: list[dict[str, Any]] = []
        for field_name, value in sorted(record.items()):
            rows.append(
                entity_field_status_row(
                    field_name,
                    value,
                    category=self.category,
                    agent_name=self.agent_name,
                ),
            )
        return rows

    def ensure_storage(self) -> None:
        """Initialize specialist storage files for this category."""
        SpecialistStorage(category=self.category)

    def run(self, state: Any) -> dict[str, Any]:
        raise NotImplementedError(
            f"{self.agent_name!r} graph run is not implemented on the base class",
        )


def _resolve_agent_for_write(agent_name: str, category: str) -> SpecialistAgent:
    import importlib

    try:
        mod = importlib.import_module(f"agents.specialists.{agent_name}")
    except ModuleNotFoundError:
        mod = None
    if mod is not None:
        agent = getattr(mod, "AGENT", None)
        if agent is not None:
            return agent
    from agents.registry import get_agent_registry

    return get_agent_registry().get_agent_instance(agent_name)


def write_bind_fields_multi(
    entity_id: str,
    normalized_fields: dict[str, str],
    *,
    resolve_owner: Callable[[str], tuple[str, str]],
    actor_kind: str,
    at: str,
) -> dict[str, str]:
    """Write bind fields across categories with rollback on partial failure."""
    by_category: dict[str, dict[str, str]] = {}
    specialists: dict[str, str] = {}
    for field, value in normalized_fields.items():
        category, specialist = resolve_owner(field)
        by_category.setdefault(category, {})[field] = value
        specialists[category] = specialist

    snapshots: dict[str, dict[str, Any] | None] = {}
    saved: list[str] = []
    merged: dict[str, str] = {}
    try:
        for category, fields in by_category.items():
            agent = _resolve_agent_for_write(specialists[category], category)
            snapshots[category] = agent.storage.load_entity(entity_id)
            merged.update(
                agent.write_fields(
                    entity_id,
                    fields,
                    actor_kind=actor_kind,
                    at=at,
                ),
            )
            saved.append(category)
    except Exception:
        for category in saved:
            agent = _resolve_agent_for_write(specialists[category], category)
            snapshot = snapshots[category]
            if snapshot is None:
                agent.storage.delete_entity(entity_id)
            else:
                agent.storage.save_entity(entity_id, snapshot)
        raise
    return merged

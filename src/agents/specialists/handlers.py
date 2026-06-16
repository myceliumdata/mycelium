"""Specialist storage handlers — implementation detail inside specialists package."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from agents.specialists.base import SpecialistStorage
from agents.specialists.fields import (
    append_version,
    current_status,
    current_value,
    current_value_matches,
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


def write_fields(
    category: str,
    specialist_name: str,
    entity_id: str,
    fields: dict[str, str],
    *,
    actor_kind: str,
    at: str | None = None,
) -> dict[str, str]:
    """Write fields to specialist storage; return current values for written keys."""
    timestamp = at or _now_iso()
    storage = SpecialistStorage(category=category)
    data = storage.load()
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
                category=category,
                specialist=specialist_name,
            ),
        }
        record[key] = append_version(record.get(key), version_body)
        written = current_value(record[key])
        if written is not None:
            current[key] = written
    storage.save(data)
    return current


def read_fields(
    category: str,
    entity_id: str,
    fields: list[str],
    *,
    include_versions: bool = False,
    include_provenance: bool | None = None,
) -> dict[str, Any]:
    """Read normalized ``FieldSnapshot`` maps for one entity."""
    with_provenance = include_versions if include_provenance is None else include_provenance
    storage = SpecialistStorage(category=category)
    record = storage.load().get("records", {}).get(entity_id, {})
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
            category=category,
            include_provenance=with_provenance,
        )
    return out


def bootstrap_entity(
    category: str,
    specialist_name: str,
    entity_id: str,
    fields: dict[str, str],
    *,
    actor_kind: str = "seed_bootstrap",
) -> dict[str, str]:
    return write_fields(
        category,
        specialist_name,
        entity_id,
        fields,
        actor_kind=actor_kind,
    )


def write_bind_fields_multi(
    entity_id: str,
    normalized_fields: dict[str, str],
    *,
    resolve_owner: Any,
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

    snapshots: dict[str, dict[str, Any]] = {}
    saved: list[str] = []
    merged: dict[str, str] = {}
    try:
        for category, fields in by_category.items():
            storage = SpecialistStorage(category=category)
            snapshots[category] = copy.deepcopy(storage.load())
            merged.update(
                write_fields(
                    category,
                    specialists[category],
                    entity_id,
                    fields,
                    actor_kind=actor_kind,
                    at=at,
                ),
            )
            saved.append(category)
    except Exception:
        for category in saved:
            SpecialistStorage(category=category).save(snapshots[category])
        raise
    return merged


def read_category_slice(
    category: str,
    entity_ids: list[str],
    *,
    bind_fields: frozenset[str] | set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return entity_id → normalized ``FieldContextSnapshot`` field maps."""
    storage = SpecialistStorage(category=category)
    records = storage.load().get("records", {})
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
                category=category,
            )
        if entity_slice:
            out[entity_id] = entity_slice
    return out


def analyze_category_storage(category: str) -> dict[str, Any]:
    """Summarize specialist storage for admin/status (no path exposure)."""
    storage = SpecialistStorage(category=category)
    strategy_name = storage.current_strategy()
    payload = storage.load()
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


def entity_field_statuses_for_category(
    category: str,
    agent_name: str,
    entity_id: str,
) -> list[dict[str, Any]]:
    """Build entity field status rows for one category."""
    storage = SpecialistStorage(category=category)
    record = storage.load().get("records", {}).get(entity_id, {})
    if not isinstance(record, dict):
        return []
    rows: list[dict[str, Any]] = []
    for field_name, value in sorted(record.items()):
        rows.append(
            entity_field_status_row(
                field_name,
                value,
                category=category,
                agent_name=agent_name,
            ),
        )
    return rows


def ensure_category_storage(category: str) -> None:
    """Initialize specialist storage files for a category."""
    SpecialistStorage(category=category)

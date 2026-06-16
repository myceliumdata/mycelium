"""Normalized read snapshots — framework-facing shapes (opaque to storage layout)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from agents.specialists.fields import (
    current_status,
    current_value,
    current_version,
    is_versioned_field,
    validate_versioned_field,
)

_BIND_FIELDS = frozenset({"name", "employer"})


def _updated_at_from_entry(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    if is_versioned_field(entry):
        version = current_version(entry)
        if isinstance(version, dict):
            raw = version.get("at")
            return str(raw) if raw else None
        return None
    raw = entry.get("at") or entry.get("researched_at")
    return str(raw) if raw else None


def _sources_from_entry(entry: Any) -> list[str]:
    if not isinstance(entry, dict):
        return []
    if is_versioned_field(entry):
        version = current_version(entry)
        if not isinstance(version, dict):
            return []
        raw_sources = version.get("sources") or []
    else:
        raw_sources = entry.get("sources") or []
    urls: list[str] = []
    for item in raw_sources:
        if isinstance(item, dict):
            url = str(item.get("url") or "").strip()
        else:
            url = str(item or "").strip()
        if url:
            urls.append(url)
    return urls


def _operator_block(entry: Any) -> dict[str, Any]:
    default = {"set": False, "value": None, "at": None, "note": None}
    if not isinstance(entry, dict) or not is_versioned_field(entry):
        return default
    version = current_version(entry)
    if not isinstance(version, dict):
        return default
    actor = version.get("actor")
    if not isinstance(actor, dict) or actor.get("kind") != "operator":
        return default
    note = version.get("note") or version.get("reason")
    return {
        "set": True,
        "value": version.get("value"),
        "at": version.get("at"),
        "note": str(note) if note else None,
    }


def field_snapshot(
    entry: Any,
    *,
    field_name: str,
    category: str,
    include_provenance: bool = False,
) -> dict[str, Any]:
    """Build a ``FieldSnapshot`` for one storage field entry."""
    status = "empty"
    value: str | None = None
    updated_at: str | None = None

    if isinstance(entry, dict):
        validate_versioned_field(entry, field_name=field_name, category=category)
        if is_versioned_field(entry):
            status = current_status(entry)
            raw_value = current_value(entry)
            value = str(raw_value) if raw_value is not None else None
            updated_at = _updated_at_from_entry(entry)
        elif entry not in ({},):
            status = "found"
            raw = entry.get("value") if "value" in entry else entry
            if raw not in (None, ""):
                value = str(raw)
                updated_at = _updated_at_from_entry(entry)
    elif entry not in (None, ""):
        status = "found"
        value = str(entry)
        updated_at = None

    snap: dict[str, Any] = {
        "value": value,
        "status": status,
        "updated_at": updated_at,
    }
    if include_provenance:
        provenance: dict[str, Any] | None = None
        if isinstance(entry, dict) and is_versioned_field(entry):
            provenance = {
                "current_version_id": entry.get("current_version_id"),
                "versions": deepcopy(list(entry.get("versions") or [])),
            }
        snap["provenance"] = provenance
    return snap


def _is_context_snapshot(entry: dict[str, Any]) -> bool:
    return "operator" in entry and "sources" in entry and "status" in entry


def field_context_snapshot(
    entry: Any,
    *,
    field_name: str,
    category: str,
) -> dict[str, Any]:
    """Build a ``FieldContextSnapshot`` for graph/research context."""
    if isinstance(entry, dict) and _is_context_snapshot(entry):
        return dict(entry)
    base = field_snapshot(entry, field_name=field_name, category=category)
    return {
        "value": base["value"],
        "status": base["status"],
        "sources": _sources_from_entry(entry),
        "updated_at": base["updated_at"],
        "operator": _operator_block(entry),
    }


def normalize_context_fields(
    row: dict[str, Any],
    *,
    category: str,
) -> dict[str, Any]:
    """Normalize one entity's specialist storage row for research context."""
    out: dict[str, Any] = {}
    for field_name, entry in sorted(row.items()):
        if field_name in _BIND_FIELDS:
            continue
        out[field_name] = field_context_snapshot(
            entry,
            field_name=field_name,
            category=category,
        )
    return out


def entity_field_status_row(
    field_name: str,
    entry: Any,
    *,
    category: str,
    agent_name: str,
) -> dict[str, Any]:
    """Admin/status row aligned with ``FieldSnapshot``."""
    snap = field_snapshot(
        entry,
        field_name=field_name,
        category=category,
        include_provenance=True,
    )
    provenance = snap.get("provenance") or {}
    versions = provenance.get("versions") if isinstance(provenance, dict) else None
    return {
        "field": field_name,
        "category": category,
        "agent": agent_name,
        "status": snap["status"],
        "value": snap["value"],
        "versions": tuple(versions or ()),
    }

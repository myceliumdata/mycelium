"""Research persistence handlers — specialist storage only."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.specialists.base import SpecialistStorage
from agents.specialists.fields import (
    append_version,
    current_status,
    ensure_versioned_for_write,
    field_has_value,
    is_versioned_field,
    research_actor,
    update_current_pending,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_pending(
    entry: dict[str, Any] | None,
    *,
    at: str,
    last_error: str,
    started_at: str | None,
    category: str,
    specialist_name: str,
) -> dict[str, Any]:
    shell = ensure_versioned_for_write(entry)
    from agents.specialists.fields import current_version as cv

    version = cv(shell)
    actor = research_actor(category=category, specialist_name=specialist_name)
    if version is not None and version.get("status") == "pending":
        return update_current_pending(shell, at=at, last_error=last_error)
    started = started_at or at
    body = {
        "at": at,
        "status": "pending",
        "started_at": started,
        "last_error": last_error,
        "actor": actor,
    }
    return append_version(shell, body)


def _pending_started_at(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    if is_versioned_field(entry):
        from agents.specialists.fields import current_version as cv

        version = cv(entry)
        if version is None:
            return None
        return str(version.get("started_at") or version.get("at") or "") or None
    raw = entry.get("started_at")
    return str(raw) if raw else None


def _current_actor_kind(entry: Any) -> str | None:
    if not isinstance(entry, dict) or not is_versioned_field(entry):
        return None
    from agents.specialists.fields import current_version as cv

    version = cv(entry)
    if not isinstance(version, dict):
        return None
    actor = version.get("actor")
    if isinstance(actor, dict):
        raw = actor.get("kind")
        return str(raw) if raw else None
    return None


def _persist_field_version(
    existing: Any,
    version_body: dict[str, Any],
) -> dict[str, Any]:
    if field_has_value(existing) and _current_actor_kind(existing) != "operator":
        return existing if isinstance(existing, dict) else ensure_versioned_for_write(None)
    shell = ensure_versioned_for_write(existing)
    from agents.specialists.fields import current_version as cv

    current = cv(shell)
    new_status = version_body.get("status")
    if current is None:
        return append_version(shell, version_body)
    if current.get("status") == "pending" and new_status == "pending":
        return update_current_pending(
            shell,
            at=str(version_body.get("at") or ""),
            last_error=str(version_body.get("last_error") or ""),
        )
    return append_version(shell, version_body)


def mark_pending(
    category: str,
    specialist_name: str,
    entity_id: str,
    fields: list[str],
    *,
    last_error: str,
) -> None:
    storage = SpecialistStorage(category=category)
    data = storage.load()
    records = data.setdefault("records", {})
    rec = records.setdefault(entity_id, {})
    now = _now_iso()
    for fld in fields:
        existing = rec.get(fld)
        if field_has_value(existing):
            continue
        started = _pending_started_at(existing)
        rec[fld] = _write_pending(
            existing if isinstance(existing, dict) else None,
            at=now,
            last_error=last_error,
            started_at=started,
            category=category,
            specialist_name=specialist_name,
        )
    storage.save(data)


def persist_proposal(
    category: str,
    specialist_name: str,
    entity_id: str,
    proposal: Any,
    *,
    allowed: set[str],
    min_confidence: float,
    validate_and_build: Any,
) -> tuple[list[str], list[str]]:
    """Persist research proposal; ``validate_and_build`` supplied by tools.research."""
    storage = SpecialistStorage(category=category)
    data = storage.load()
    records = data.setdefault("records", {})
    rec = records.setdefault(entity_id, {})
    updated: list[str] = []
    errors: list[str] = []
    now = _now_iso()
    proposals_by_field = {p.field.strip().lower(): p for p in proposal.fields}
    for fld in sorted(allowed):
        existing = rec.get(fld)
        started = _pending_started_at(existing)
        fp = proposals_by_field.get(fld)
        if fp is None:
            msg = f"No proposal returned for field {fld!r}"
            errors.append(msg)
            rec[fld] = _write_pending(
                existing if isinstance(existing, dict) else None,
                at=now,
                last_error=msg,
                started_at=started,
                category=category,
                specialist_name=specialist_name,
            )
            continue
        version_body, err = validate_and_build(
            fp,
            allowed=allowed,
            min_confidence=min_confidence,
            category=category,
            specialist_name=specialist_name,
        )
        if err:
            errors.append(err)
            rec[fld] = _write_pending(
                existing if isinstance(existing, dict) else None,
                at=now,
                last_error=err,
                started_at=started,
                category=category,
                specialist_name=specialist_name,
            )
            continue
        if version_body is not None:
            rec[fld] = _persist_field_version(existing, version_body)
            if current_status(rec[fld]) in ("found", "na"):
                updated.append(fld)

    for fld in sorted(allowed):
        entry = rec.get(fld)
        status = current_status(entry) if isinstance(entry, dict) else "empty"
        if status in ("found", "na"):
            continue
        if status == "pending" and isinstance(entry, dict):
            from agents.specialists.fields import current_version as cv

            version = cv(entry)
            if version and version.get("last_error"):
                continue
        msg = f"Field {fld!r} missing after research persist"
        errors.append(msg)
        started = _pending_started_at(entry)
        rec[fld] = _write_pending(
            entry if isinstance(entry, dict) else None,
            at=now,
            last_error=msg,
            started_at=started,
            category=category,
            specialist_name=specialist_name,
        )

    storage.save(data)
    return updated, errors


def append_research_audit(
    category: str,
    specialist_name: str,
    entity_id: str,
    *,
    fields_updated: list[str],
    tool_calls_count: int,
    errors: list[str],
    context_bind: dict[str, str] | None = None,
) -> None:
    storage = SpecialistStorage(category=category)
    data = storage.load()
    meta = data.setdefault("meta", {})
    if not isinstance(meta, dict):
        return
    audit = meta.setdefault("research_audit", [])
    if not isinstance(audit, list):
        return
    entry: dict[str, Any] = {
        "at": _now_iso(),
        "category": category,
        "specialist": specialist_name,
        "person_id": entity_id,
        "fields_updated": fields_updated,
        "tool_calls_count": tool_calls_count,
        "errors": errors,
    }
    if context_bind is not None:
        entry["context_bind"] = context_bind
    audit.append(entry)
    storage.save(data)

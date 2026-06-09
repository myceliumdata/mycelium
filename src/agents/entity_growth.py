"""Registry attribution after successful specialist research (entity protocol slice 8)."""

from __future__ import annotations

import ast
import re
from datetime import datetime, timezone
from typing import Any

from agents.entity_registry import get_entity_registry
from agents.specialists.base import SpecialistStorage

_UPDATED_FIELDS_RE = re.compile(r"updated=(\[[^\]]*\])")


def parse_research_fields_updated(audit_log: list[str]) -> list[str]:
    """Extract field names written in the latest research audit line."""
    for line in reversed(audit_log):
        match = _UPDATED_FIELDS_RE.search(line)
        if not match:
            continue
        try:
            parsed = ast.literal_eval(match.group(1))
        except (ValueError, SyntaxError):
            continue
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def apply_registry_research_attribution(
    *,
    entity_id: str | None,
    contributions: list[dict[str, Any]],
) -> list[str]:
    """Update registry ``attr_sources`` / ``last_researched_at`` for this research pass."""
    if not entity_id:
        return []

    entity_registry = get_entity_registry()
    entity = entity_registry.lookup_by_id(entity_id)
    if entity is None:
        return []

    updates: dict[str, tuple[str, str]] = {}
    fallback_ts = datetime.now(timezone.utc).isoformat()

    for contrib in contributions:
        specialist_contrib = contrib.get("specialist_contrib") or {}
        category = specialist_contrib.get("category")
        if not category:
            continue
        researched_fields = parse_research_fields_updated(contrib.get("audit_log") or [])
        if not researched_fields:
            continue
        try:
            storage = SpecialistStorage(category=str(category))
            record = storage.load().get("records", {}).get(entity_id, {})
        except OSError:
            record = {}
        for field in researched_fields:
            entry = record.get(field) if isinstance(record, dict) else None
            timestamp = fallback_ts
            if isinstance(entry, dict) and entry.get("researched_at"):
                timestamp = str(entry["researched_at"])
            updates[field] = (str(category), timestamp)

    if not updates:
        return []

    entity_registry.record_research_attribution(entity_id, updates)
    attrs = ", ".join(sorted(updates))
    return [f"entity_growth: attributed registry attrs ({attrs}) for id={entity_id!r}."]

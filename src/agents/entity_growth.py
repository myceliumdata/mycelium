"""Registry attribution after successful specialist research (entity protocol slice 8)."""

from __future__ import annotations

import ast
import re
from datetime import datetime, timezone
from typing import Any

from agents.entity_registry import get_entity_registry
from agents.registry import get_agent_registry
from agents.specialists.protocol import dispatch_read_fields

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


def _agent_for_category(category: str) -> str | None:
    from agents.classification import get_category_tree

    categories = get_category_tree().get_categories()
    cat = categories.get(category)
    if cat is not None and cat.assigned_agent:
        return cat.assigned_agent
    registry = get_agent_registry()
    for agent in registry.list_agents():
        if agent.get("category") == category:
            name = agent.get("name")
            return str(name) if name else None
    return None


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
        contrib_entity = specialist_contrib.get("id") or contrib.get("entity_id")
        if contrib_entity and str(contrib_entity) != entity_id:
            continue
        category = specialist_contrib.get("category")
        if not category:
            continue
        researched_fields = list(
            contrib.get("researched_fields")
            or specialist_contrib.get("researched_fields")
            or [],
        )
        if not researched_fields:
            researched_fields = parse_research_fields_updated(
                contrib.get("audit_log") or [],
            )
        if not researched_fields:
            continue
        agent_name = _agent_for_category(str(category))
        record: dict[str, Any] = {}
        if agent_name:
            read = dispatch_read_fields(
                agent_name,
                entity_id,
                researched_fields,
                include_versions=True,
            )
            record = read
        for field in researched_fields:
            entry = record.get(field) if isinstance(record, dict) else None
            timestamp = fallback_ts
            if isinstance(entry, dict):
                updated_at = entry.get("updated_at")
                if updated_at:
                    timestamp = str(updated_at)
            updates[field] = (str(category), timestamp)

    if not updates:
        return []

    entity_registry.record_research_attribution(entity_id, updates)
    attrs = ", ".join(sorted(updates))
    return [f"entity_growth: attributed registry attrs ({attrs}) for id={entity_id!r}."]

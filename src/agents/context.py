"""Build specialist context: read-only bind fields + extended-attrs-only storage."""

from __future__ import annotations

from typing import Any

from agents.entity_registry import get_entity_registry, registry_entity_to_match
from agents.registry import get_agent_registry
from agents.specialists.protocol import dispatch_read_category_slice
from network.mvr import load_mvr, mvr_bind_field_set


def reset_context_builder() -> None:
    """No-op reset for test symmetry with other singletons."""
    return None


def get_context_builder() -> "ContextBuilder":
    return ContextBuilder()


def bind_from_record(
    record: dict[str, Any],
    *,
    bind_fields: list[str] | None = None,
) -> dict[str, str | None]:
    """Read-only bind slice from a resolved entity row (active MVR bind fields)."""
    fields = bind_fields
    if fields is None:
        fields = list(load_mvr().bind_fields)
    out: dict[str, str | None] = {}
    for raw_field in fields:
        key = raw_field.strip().lower()
        if not key:
            continue
        raw = record.get(key)
        if raw is None:
            out[key] = None
        else:
            text = str(raw).strip()
            out[key] = text if text else None
    return out


def strip_bind_fields(
    record: dict[str, Any],
    *,
    bind_fields: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Return specialist storage fields only (ignore MVR bind keys on read)."""
    skip = bind_fields if bind_fields is not None else mvr_bind_field_set()
    return {key: value for key, value in record.items() if key not in skip}


def planner_context(
    *,
    matched: list[dict[str, Any]] | dict[str, Any],
    ids: list[str],
    specialists_to_invoke: list[str],
    contributions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Supervisor/validate planning context (entity_id + bind before build_context)."""
    rows = matched if isinstance(matched, list) else [matched]
    entity_id: str | None = None
    bind: dict[str, str | None] | None = None
    if len(rows) == 1:
        row = rows[0]
        entity_id = str(row.get("id") or "") or None
        bind = bind_from_record(row)
    return {
        "entity_id": entity_id,
        "bind": bind,
        "specialists": {},
        "_meta": {
            "ids": ids,
            "specialists_to_invoke": specialists_to_invoke,
            "contributions": list(contributions or []),
        },
    }


class ContextBuilder:
    """Synchronous context assembly from registry rows + specialist dispatch reads."""

    def build_full_context(
        self,
        ids: list[str],
        *,
        matched_records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        mvr = load_mvr()
        bind_fields = mvr_bind_field_set(mvr)
        resolved = self._resolve_identity_rows(ids, matched_records=matched_records)
        entity_id: str | None = None
        bind: dict[str, str | None] | None = None
        if len(resolved) == 1:
            row = resolved[0]
            entity_id = str(row.get("id") or "") or None
            bind = bind_from_record(row, bind_fields=list(mvr.bind_fields))

        specialist_part: dict[str, Any] = {}
        registry = get_agent_registry()
        for agent in registry.list_agents():
            if not agent.get("is_generated"):
                continue
            category = agent.get("category")
            agent_name = agent.get("name")
            if not category or not agent_name:
                continue
            try:
                cat_slice = dispatch_read_category_slice(
                    str(agent_name),
                    str(category),
                    ids,
                    bind_fields=bind_fields,
                )
                if cat_slice:
                    specialist_part[str(category)] = cat_slice
            except (OSError, ValueError):
                continue

        return {
            "entity_id": entity_id,
            "bind": bind,
            "specialists": specialist_part,
        }

    def _resolve_identity_rows(
        self,
        ids: list[str],
        *,
        matched_records: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        if matched_records is not None:
            return [row for row in matched_records if isinstance(row, dict)]
        registry = get_entity_registry()
        rows: list[dict[str, Any]] = []
        for entity_id in ids:
            entity = registry.lookup_by_id(entity_id)
            if entity is not None:
                rows.append(registry_entity_to_match(entity, mvr=registry._mvr))
        return rows

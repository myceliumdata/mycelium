"""Build specialist context: read-only bind fields + extended-attrs-only storage.

TODO: Eventually specialists should retrieve context from peer agents instead of the
supervisor assembling and passing storage snapshots on every invocation.
"""

from __future__ import annotations

from typing import Any

from agents.entity_registry import get_entity_registry, registry_entity_to_match
from agents.registry import get_agent_registry
from agents.specialists.base import SpecialistStorage

BIND_FIELDS = frozenset({"name", "employer"})


def reset_context_builder() -> None:
    """No-op reset for test symmetry with other singletons."""
    return None


def get_context_builder() -> "ContextBuilder":
    return ContextBuilder()


def bind_from_record(record: dict[str, Any]) -> dict[str, str | None]:
    """Read-only bind slice (name, employer) from a resolved entity row."""
    return {
        "name": str(record.get("name") or ""),
        "employer": record.get("employer"),
    }


def strip_bind_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Return specialist storage fields only (ignore legacy name/employer on read)."""
    return {key: value for key, value in record.items() if key not in BIND_FIELDS}


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
    """Synchronous context assembly from registry rows + specialist JSON stores."""

    def build_full_context(
        self,
        ids: list[str],
        *,
        seed_records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        resolved = self._resolve_identity_rows(ids, matched_records=seed_records)
        entity_id: str | None = None
        bind: dict[str, str | None] | None = None
        if len(resolved) == 1:
            row = resolved[0]
            entity_id = str(row.get("id") or "") or None
            bind = bind_from_record(row)

        specialist_part: dict[str, Any] = {}
        registry = get_agent_registry()
        for agent in registry.list_agents():
            if not agent.get("is_generated"):
                continue
            category = agent.get("category")
            if not category:
                continue
            try:
                store = SpecialistStorage(category=category)
                payload = store.load()
                records = payload.get("records", {})
                cat_slice: dict[str, Any] = {}
                for pid in ids:
                    if pid in records:
                        cat_slice[pid] = strip_bind_fields(records[pid])
                if cat_slice:
                    specialist_part[category] = cat_slice
            except OSError:
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
                rows.append(registry_entity_to_match(entity))
        return rows

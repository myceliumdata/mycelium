"""Generic registry bridge helpers for pack specialists."""

from __future__ import annotations

from agents.entity_registry import get_entity_registry


def entity_source_key(
    entity_id: str,
    key: str,
    *,
    record_type: str | None = None,
) -> str | None:
    """Return a namespaced source key value for a registry entity."""
    entity = get_entity_registry(record_type=record_type).lookup_by_id(entity_id)
    if entity is None:
        return None
    raw = entity.source_keys.get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None

"""Per-field inverted indexes on registry MVR bind fields (MVR redesign M4).

Indexes are rebuilt in memory whenever ``entities.json`` is loaded or written.
Normalization for index keys: strip, lower-case, collapse internal whitespace,
and remove apostrophe / hyphen characters (aligned with ``bind_index`` name rules).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.entity_registry import RegistryEntity


def normalize_field_index_value(value: str) -> str:
    """Normalize a field value for exact index lookup (no fuzzy widening)."""
    text = value.strip().lower()
    for ch in ("'", "-", "\u2019"):
        text = text.replace(ch, "")
    return " ".join(text.split())


def _entity_field_value(entity: RegistryEntity, field: str) -> str | None:
    """Read a bind-field value from a registry row (supports all ``RegistryEntity`` attrs)."""
    key = field.strip().lower()
    if key == "name":
        raw = entity.name
    elif key == "employer":
        raw = entity.employer
    elif hasattr(entity, key):
        raw = getattr(entity, key)
    else:
        return None
    if raw is None or not str(raw).strip():
        return None
    return str(raw)


def build_field_indexes(
    entities: dict[str, RegistryEntity],
    bind_fields: list[str],
) -> dict[str, dict[str, list[str]]]:
    """Build field → normalized value → entity id lists from registry rows."""
    fields = [field.strip().lower() for field in bind_fields if field.strip()]
    indexes: dict[str, dict[str, list[str]]] = {field: {} for field in fields}
    for entity_id, entity in entities.items():
        for field in fields:
            raw = _entity_field_value(entity, field)
            if raw is None:
                continue
            norm = normalize_field_index_value(raw)
            bucket = indexes[field]
            bucket.setdefault(norm, []).append(entity_id)
    return indexes


def intersect_lookup(
    indexes: dict[str, dict[str, list[str]]],
    lookup: dict[str, str],
    bind_fields: list[str],
) -> list[str]:
    """Return entity ids matching all lookup fields (AND), in stable sorted order."""
    if not lookup:
        return []
    allowed = {field.strip().lower() for field in bind_fields if field.strip()}
    sets: list[set[str]] = []
    for field, value in lookup.items():
        field_key = field.strip().lower()
        if field_key not in allowed:
            return []
        if not str(value).strip():
            return []
        norm = normalize_field_index_value(str(value))
        ids = indexes.get(field_key, {}).get(norm, [])
        if not ids:
            return []
        sets.append(set(ids))
    if not sets:
        return []
    matched = sets[0]
    for candidate in sets[1:]:
        matched &= candidate
    return sorted(matched)

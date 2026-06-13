"""Unified MVR bind-field writes (Program 2 Slice 1).

Canonical values and versions[] live in taxonomy-owned specialist storage;
``entities.json`` holds cache, protocol fields, and derived indexes.

Multi-category writes snapshot specialist payloads before save and best-effort
rollback prior categories if a later save fails (Program 2 polish P4).
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from agents.entity_registry import (
    EntityRegistry,
    RegistryEntity,
    get_entity_registry,
    make_bind_key,
)
from agents.specialist_fields import append_version, current_value_matches
from agents.specialists.base import SpecialistStorage
from network.mvr import load_mvr, normalized_lookup_values


def resolve_attribute_owner(attribute: str) -> tuple[str, str]:
    """Return ``(category, assigned_agent)`` from ``categories.json`` ``attribute_map``."""
    from agents.classification import get_category_tree

    normalized = attribute.strip().lower()
    if not normalized:
        raise ValueError("attribute name is required")

    tree = get_category_tree()
    category = tree.mapped_category(normalized)
    if not category:
        raise ValueError(
            f"MVR bind field {attribute!r} is not mapped in categories.json attribute_map",
        )

    categories = tree.get_categories()
    cat = categories.get(category)
    if cat is None or not cat.assigned_agent:
        raise ValueError(
            f"category {category!r} has no assigned_agent for attribute {attribute!r}",
        )
    return category, cat.assigned_agent


def _actor_body(*, kind: str, category: str, specialist: str) -> dict[str, str]:
    return {"kind": kind, "category": category, "specialist": specialist}


def _apply_specialist_bind_writes(
    entity_id: str,
    normalized_fields: dict[str, str],
    *,
    actor_kind: str,
    at: str,
) -> None:
    """Mutate specialist storage for bind fields; rollback on partial save failure."""
    snapshots: dict[str, dict[str, Any]] = {}
    pending: dict[str, dict[str, Any]] = {}

    for field, value in normalized_fields.items():
        category, specialist = resolve_attribute_owner(field)
        if category not in pending:
            storage = SpecialistStorage(category)
            loaded = storage.load()
            snapshots[category] = copy.deepcopy(loaded)
            pending[category] = loaded

        data = pending[category]
        records = data.setdefault("records", {})
        record = records.setdefault(entity_id, {})
        if current_value_matches(record.get(field), value):
            continue
        version_body: dict[str, Any] = {
            "at": at,
            "status": "found",
            "value": value,
            "actor": _actor_body(
                kind=actor_kind,
                category=category,
                specialist=specialist,
            ),
        }
        record[field] = append_version(record.get(field), version_body)

    saved: list[str] = []
    try:
        for category, data in pending.items():
            SpecialistStorage(category).save(data)
            saved.append(category)
    except Exception:
        for category in saved:
            SpecialistStorage(category).save(snapshots[category])
        raise


def _apply_cache_field(entity: RegistryEntity, field: str, value: str) -> None:
    """Denormalize MVR bind values on the registry row for hot reads.

    CRM v1 caches ``name`` and ``employer`` columns only; additional
    ``mvr.bind_fields`` are stored in specialist storage + ``attr_sources``.
    """
    key = field.strip().lower()
    text = value.strip()
    if key == "name":
        entity.name = text
    elif key == "employer":
        entity.employer = text or None


def _cache_values(entity: RegistryEntity) -> dict[str, str]:
    """Snapshot cached bind columns used for ``bind_index`` (CRM v1: name + employer)."""
    return {
        "name": entity.name,
        "employer": entity.employer or "",
    }


def write_bind_fields(
    entity_id: str,
    fields: dict[str, str],
    *,
    actor_kind: str,
    source: str | None = None,
    validation_state: str | None = None,
    registry: EntityRegistry | None = None,
) -> RegistryEntity:
    """Write MVR bind fields to specialist storage and sync registry cache + indexes."""
    reg = registry if registry is not None else get_entity_registry()
    entity = reg.lookup_by_id(entity_id)
    if entity is None:
        raise ValueError(f"Unknown registry entity: {entity_id}")

    mvr = load_mvr()
    allowed = {field.strip().lower() for field in mvr.bind_fields if field.strip()}
    normalized_fields = {
        key.strip().lower(): value.strip()
        for key, value in fields.items()
        if key.strip() and value.strip()
    }
    if not normalized_fields:
        raise ValueError("write_bind_fields requires at least one non-empty MVR field")

    unknown = set(normalized_fields) - allowed
    if unknown:
        raise ValueError(f"fields not in mvr.bind_fields: {sorted(unknown)}")

    old_values = _cache_values(entity)
    old_key = make_bind_key(old_values["name"], old_values["employer"])
    now = datetime.now(timezone.utc).isoformat()

    _apply_specialist_bind_writes(
        entity_id,
        normalized_fields,
        actor_kind=actor_kind,
        at=now,
    )
    for field in normalized_fields:
        category = resolve_attribute_owner(field)[0]
        entity.attr_sources[field] = category
        _apply_cache_field(entity, field, normalized_fields[field])

    if validation_state is not None:
        entity.validation_state = validation_state
        if validation_state == "provisional":
            entity.field_states = {field: "provisional" for field in normalized_fields}
        else:
            entity.field_states = {field: "validated" for field in normalized_fields}

    if source is not None:
        entity.source = source

    new_key = make_bind_key(entity.name, entity.employer or "")
    if new_key != old_key:
        reg.pop_bind_index(old_values["name"], old_values["employer"])

    reg.assign_bind_index(entity_id, entity.name, entity.employer or "")
    reg.save_entity(entity)
    return entity


def ensure_entity_bind_fields(
    fields: dict[str, str],
    *,
    source: str,
    validation_state: str,
    actor_kind: str | None = None,
    registry: EntityRegistry | None = None,
) -> tuple[RegistryEntity, bool]:
    """Allocate entity id when needed; unified write for all MVR bind fields present."""
    reg = registry if registry is not None else get_entity_registry()
    values = normalized_lookup_values({str(k): str(v) for k, v in fields.items()})
    mvr = load_mvr()
    bind_values = {
        field.strip().lower(): values[field.strip().lower()]
        for field in mvr.bind_fields
        if field.strip().lower() in values
    }
    if "name" not in bind_values:
        raise ValueError("bind fields require lookup.name")

    name = bind_values["name"]
    employer = bind_values.get("employer", "")
    resolved_actor = actor_kind or (
        "seed_bootstrap" if source == "seed_bootstrap" else "bind"
    )

    existing = reg.lookup_by_bind_key(name, employer)
    if existing is not None:
        return existing, True

    now = datetime.now(timezone.utc).isoformat()
    entity_id = str(uuid.uuid4())
    entity = RegistryEntity(
        id=entity_id,
        name=name,
        employer=employer or None,
        validation_state=validation_state,
        field_states={},
        source=source,
        created_at=now,
    )
    reg.register_entity(entity)
    write_bind_fields(
        entity_id,
        bind_values,
        actor_kind=resolved_actor,
        source=source,
        validation_state=validation_state,
        registry=reg,
    )
    updated = reg.lookup_by_id(entity_id)
    assert updated is not None
    return updated, False


def ensure_entity_bind(
    name: str,
    employer: str,
    *,
    source: str,
    validation_state: str,
    actor_kind: str | None = None,
    registry: EntityRegistry | None = None,
) -> tuple[RegistryEntity, bool]:
    """CRM-shaped bind helper — delegates to ``ensure_entity_bind_fields``."""
    return ensure_entity_bind_fields(
        {"name": name, "employer": employer},
        source=source,
        validation_state=validation_state,
        actor_kind=actor_kind,
        registry=registry,
    )

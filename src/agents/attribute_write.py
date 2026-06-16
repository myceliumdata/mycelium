"""Unified MVR bind-field writes (Program 2 Slice 1).

Canonical values and versions[] live in taxonomy-owned specialist storage;
``entities.json`` holds cache, protocol fields, and derived indexes.

Framework dispatches specialist writes via ``agents.specialists.protocol``;
registry cache/indexes sync from returned values only.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from agents.entity_registry import (
    EntityRegistry,
    RegistryEntity,
    get_entity_registry,
    make_bind_key,
    require_full_bind_values,
)
from agents.specialists.protocol import (
    dispatch_write_bind_fields_multi,
    resolve_owner as _resolve_owner,
)
from network.mvr import load_mvr, normalized_lookup_values


def resolve_attribute_owner(attribute: str) -> tuple[str, str]:
    """Return ``(category, assigned_agent)`` from ``categories.json`` ``attribute_map``."""
    return _resolve_owner(attribute)


def _apply_cache_field(entity: RegistryEntity, field: str, value: str) -> None:
    """Update ``bind_values`` cache for an MVR bind field."""
    entity.bind_values[field.strip().lower()] = value.strip()


def _cache_values(entity: RegistryEntity, mvr: Any | None = None) -> dict[str, str]:
    """Snapshot bind_values used for ``bind_index`` (all ``mvr.bind_fields``)."""
    policy = mvr if mvr is not None else load_mvr()
    return require_full_bind_values(entity.bind_values, list(policy.bind_fields))


def write_bind_fields(
    entity_id: str,
    fields: dict[str, str],
    *,
    actor_kind: str,
    source: str | None = None,
    validation_state: str | None = None,
    registry: EntityRegistry | None = None,
) -> RegistryEntity:
    """Write MVR bind fields via specialist dispatch; sync registry cache + indexes."""
    reg = registry if registry is not None else get_entity_registry()
    entity = reg.lookup_by_id(entity_id)
    if entity is None:
        raise ValueError(f"Unknown registry entity: {entity_id}")

    mvr = reg._mvr
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

    old_values: dict[str, str] | None = None
    old_key: str | None = None
    try:
        old_values = _cache_values(entity, mvr)
        old_key = make_bind_key(old_values, list(mvr.bind_fields))
    except ValueError:
        pass
    now = datetime.now(timezone.utc).isoformat()

    returned = dispatch_write_bind_fields_multi(
        entity_id,
        normalized_fields,
        actor_kind=actor_kind,
        at=now,
    )
    for field in normalized_fields:
        category = resolve_attribute_owner(field)[0]
        entity.attr_sources[field] = category
        cached = returned.get(field, normalized_fields[field])
        _apply_cache_field(entity, field, cached)

    if validation_state is not None:
        entity.validation_state = validation_state
        if validation_state == "provisional":
            entity.field_states = {field: "provisional" for field in normalized_fields}
        else:
            entity.field_states = {field: "validated" for field in normalized_fields}

    if source is not None:
        entity.source = source

    new_values = _cache_values(entity, mvr)
    new_key = make_bind_key(new_values, list(mvr.bind_fields))
    if old_values is not None and new_key != old_key:
        reg.pop_bind_index(old_values)

    reg.assign_bind_index(entity_id, new_values)
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
    mvr = reg._mvr
    bind_values = require_full_bind_values(values, list(mvr.bind_fields))

    resolved_actor = actor_kind or (
        "seed_bootstrap" if source == "seed_bootstrap" else "bind"
    )

    existing = reg.lookup_by_bind_values(bind_values)
    if existing is not None:
        if source == "seed_bootstrap":
            write_bind_fields(
                existing.id,
                bind_values,
                actor_kind=resolved_actor,
                source=source,
                validation_state=validation_state,
                registry=reg,
            )
            updated = reg.lookup_by_id(existing.id)
            return updated if updated is not None else existing, True
        return existing, True

    now = datetime.now(timezone.utc).isoformat()
    entity_id = str(uuid.uuid4())
    entity = RegistryEntity(
        id=entity_id,
        bind_values={},
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

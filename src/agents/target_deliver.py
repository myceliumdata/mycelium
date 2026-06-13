"""Step-2 target protocol deliver (MVR redesign M5/M7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.entity_registry import (
    RegistryEntity,
    get_entity_registry,
    registry_entity_to_match,
)
from models.state import normalized_requested_attributes
from network.delivery import DeliveryScope, get_delivery_store
from network.mvr import normalized_lookup_values


@dataclass(frozen=True)
class DeliveryLoadResult:
    kind: str
    scope: DeliveryScope | None = None
    matched_records: list[dict[str, Any]] | None = None


def load_delivery_scope(delivery_id: str) -> DeliveryLoadResult:
    """Load a non-expired delivery scope and hydrate registry match rows."""
    scope = get_delivery_store().get(delivery_id.strip())
    if scope is None:
        return DeliveryLoadResult(kind="not_found")

    if scope.create_on_deliver and not scope.entity_ids:
        return DeliveryLoadResult(
            kind="create_pending",
            scope=scope,
            matched_records=[],
        )

    registry = get_entity_registry()
    matched: list[dict[str, Any]] = []
    for entity_id in scope.entity_ids:
        entity = registry.lookup_by_id(entity_id)
        if entity is None:
            return DeliveryLoadResult(kind="not_found")
        matched.append(registry_entity_to_match(entity))

    if not matched:
        return DeliveryLoadResult(kind="not_found")

    return DeliveryLoadResult(kind="loaded", scope=scope, matched_records=matched)


def delivery_scope_has_attributes(scope: DeliveryScope) -> bool:
    return bool(normalized_requested_attributes(scope.requested_attributes))


def bind_provisional_from_scope(scope: DeliveryScope) -> RegistryEntity:
    """Create or reuse a provisional registry row from a create-on-deliver scope."""
    from network.mvr import load_mvr

    values = normalized_lookup_values(
        {str(k): str(v) for k, v in scope.lookup.items()},
    )
    mvr = load_mvr()
    name = values.get("name", "")
    employer = values.get("employer", "")
    for field in mvr.bind_fields:
        key = field.strip().lower()
        if key == "name":
            name = values.get(key, name)
        elif key == "employer":
            employer = values.get(key, employer)
    if not name:
        raise ValueError("create_on_deliver scope missing lookup.name")
    registry = get_entity_registry()
    entity, _duplicate = registry.bind_provisional(name, employer)
    return entity


def hydrate_matches_for_deliver(
    loaded: DeliveryLoadResult,
) -> tuple[DeliveryScope, list[dict[str, Any]], str]:
    """Return scope, match rows, and entity_resolution_kind for step-2 deliver."""
    if loaded.scope is None:
        raise ValueError("delivery scope missing")

    scope = loaded.scope
    if scope.create_on_deliver and not scope.entity_ids:
        entity = bind_provisional_from_scope(scope)
        matched = [registry_entity_to_match(entity)]
        return scope, matched, "bind_provisional"

    matched = list(loaded.matched_records or [])
    if not matched:
        raise ValueError("delivery scope has no matches")
    return scope, matched, "exact"

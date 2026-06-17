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
        matched.append(registry_entity_to_match(entity, mvr=registry._mvr))

    if not matched:
        return DeliveryLoadResult(kind="not_found")

    return DeliveryLoadResult(kind="loaded", scope=scope, matched_records=matched)


def delivery_scope_has_attributes(scope: DeliveryScope) -> bool:
    return bool(normalized_requested_attributes(scope.requested_attributes))


def bind_provisional_from_scope(scope: DeliveryScope) -> RegistryEntity:
    """Create or reuse a provisional registry row from a create-on-deliver scope."""
    from agents.attribute_write import ensure_entity_bind_fields
    from network.category_mvr_bootstrap import ensure_categories_for_mvr_bind
    from network.mvr import load_mvr
    from network.paths import NetworkPaths, resolve_network_root

    ensure_categories_for_mvr_bind(NetworkPaths.from_root(resolve_network_root()))

    lookup = normalized_lookup_values(
        {str(k): str(v) for k, v in scope.lookup.items()},
    )
    bind_fields = {
        field.strip().lower(): lookup[field.strip().lower()]
        for field in load_mvr().bind_fields
        if field.strip() and field.strip().lower() in lookup
    }
    entity, _duplicate = ensure_entity_bind_fields(
        bind_fields,
        source="query_bind",
        validation_state="provisional",
        actor_kind="bind",
    )
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

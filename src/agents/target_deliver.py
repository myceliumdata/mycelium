"""Step-2 target protocol deliver (MVR redesign M5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.entity_registry import get_entity_registry, registry_entity_to_match
from models.state import normalized_requested_attributes
from network.delivery import DeliveryScope, get_delivery_store


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

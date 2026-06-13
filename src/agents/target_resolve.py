"""Step-1 target protocol resolve (MVR redesign M4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.entity_registry import get_entity_registry
from models.state import DeliveryPayload, EntityQuery
from network.delivery import get_delivery_store, issue_delivery


@dataclass(frozen=True)
class TargetResolveResult:
    kind: str
    entity_ids: list[str]
    lookup_snapshot: dict[str, Any]
    delivery: DeliveryPayload | None = None


def resolve_target_step1(query: EntityQuery) -> TargetResolveResult:
    """Resolve step-1 target query by id or lookup AND (read-only)."""
    registry = get_entity_registry()
    entity_id = (query.id or "").strip()
    if entity_id:
        entity = registry.lookup_by_id(entity_id)
        if entity is None:
            return TargetResolveResult(
                kind="not_found",
                entity_ids=[],
                lookup_snapshot={"id": entity_id},
            )
        return TargetResolveResult(
            kind="resolved",
            entity_ids=[entity_id],
            lookup_snapshot={"id": entity_id},
        )

    if query.lookup:
        entity_ids = registry.lookup_by_target_lookup(query.lookup)
        if not entity_ids:
            return TargetResolveResult(
                kind="not_found",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
            )
        return TargetResolveResult(
            kind="resolved",
            entity_ids=entity_ids,
            lookup_snapshot=dict(query.lookup),
        )

    return TargetResolveResult(kind="not_found", entity_ids=[], lookup_snapshot={})


def issue_target_delivery(query: EntityQuery, entity_ids: list[str]) -> DeliveryPayload:
    """Issue and persist a delivery scope for a resolved step-1 query."""
    scope = issue_delivery(
        entity_ids=entity_ids,
        lookup=(
            {"id": (query.id or "").strip()}
            if (query.id or "").strip()
            else dict(query.lookup)
        ),
        requested_attributes=list(query.requested_attributes),
        provenance=bool(query.provenance),
    )
    get_delivery_store().put(scope)
    return DeliveryPayload(
        delivery_id=scope.delivery_id,
        expires_at=scope.expires_at,
    )

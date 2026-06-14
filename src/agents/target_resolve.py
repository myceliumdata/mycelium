"""Step-1 target protocol resolve (MVR redesign M4/M7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agents.entity_registry import _normalize_name_for_bind, get_entity_registry
from agents.entity_resolution import _rank_suggestions
from models.state import DeliveryPayload, EntityKeySuggestion, EntityQuery
from network.delivery import get_delivery_store, issue_delivery
from network.mvr import (
    is_full_mvr_lookup,
    load_mvr,
    missing_mvr_bind_fields,
    normalized_lookup_values,
)


@dataclass(frozen=True)
class TargetResolveResult:
    kind: str
    entity_ids: list[str]
    lookup_snapshot: dict[str, Any]
    delivery: DeliveryPayload | None = None
    create_on_deliver: bool = False
    required_fields: list[str] = field(default_factory=list)
    suggestions: list[EntityKeySuggestion] = field(default_factory=list)


def _same_name_different_employer_suggestions(
    lookup: dict[str, str],
) -> list[EntityKeySuggestion]:
    norm = normalized_lookup_values(lookup)
    name = norm.get("name")
    employer = norm.get("employer")
    if not name or not employer:
        return []

    lookup_employer = _normalize_name_for_bind(employer)
    suggestions: list[EntityKeySuggestion] = []
    for entity in get_entity_registry().lookup_by_name(name):
        entity_employer = _normalize_name_for_bind(entity.employer or "")
        if entity_employer == lookup_employer:
            continue
        suggestions.append(
            EntityKeySuggestion(
                entity_key=entity.name,
                id=entity.id,
                name=entity.name,
                employer=entity.employer,
                score=1.0,
                reason="same_name_different_employer",
            ),
        )
    return suggestions


def _lookup_suggestions_for_full_mvr(
    lookup: dict[str, str],
) -> list[EntityKeySuggestion]:
    same_name = _same_name_different_employer_suggestions(lookup)
    if same_name:
        return same_name

    norm = normalized_lookup_values(lookup)
    name_value = norm.get("name")
    if not name_value:
        return []
    return _rank_suggestions(name_value)


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
        if entity_ids:
            return TargetResolveResult(
                kind="resolved",
                entity_ids=entity_ids,
                lookup_snapshot=dict(query.lookup),
            )

        mvr = load_mvr()
        if not is_full_mvr_lookup(query.lookup, mvr):
            missing = missing_mvr_bind_fields(query.lookup, mvr=mvr)
            return TargetResolveResult(
                kind="lookup_incomplete",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                required_fields=missing,
            )

        if query.confirm_new_entity:
            return TargetResolveResult(
                kind="create_pending",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                create_on_deliver=True,
            )

        suggestions = _lookup_suggestions_for_full_mvr(query.lookup)
        if suggestions:
            return TargetResolveResult(
                kind="lookup_suggested",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                suggestions=suggestions,
            )

        return TargetResolveResult(
            kind="create_pending",
            entity_ids=[],
            lookup_snapshot=dict(query.lookup),
            create_on_deliver=True,
        )

    return TargetResolveResult(kind="not_found", entity_ids=[], lookup_snapshot={})


def issue_target_delivery(
    query: EntityQuery,
    entity_ids: list[str],
    *,
    create_on_deliver: bool = False,
) -> DeliveryPayload:
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
        create_on_deliver=create_on_deliver,
    )
    get_delivery_store().put(scope)
    return DeliveryPayload.from_scope(scope)

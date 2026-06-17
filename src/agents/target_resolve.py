"""Step-1 target protocol resolve (MVR redesign M4/M7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agents.entity_registry import get_entity_registry
from agents.field_index import normalize_field_index_value
from agents.entity_resolution import (
    _rank_bind_field_fuzzy_suggestions,
    _rank_suggestions,
)
from models.state import DeliveryPayload, EntityQuery, LookupSuggestion, lookup_suggestion
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
    suggestions: list[LookupSuggestion] = field(default_factory=list)


def _same_bind_field_conflict_suggestions(
    lookup: dict[str, str],
) -> list[LookupSuggestion]:
    norm = normalized_lookup_values(lookup)
    mvr = load_mvr()
    bind_fields = [f.strip().lower() for f in mvr.bind_fields if f.strip()]
    if len(bind_fields) < 2 or not all(field in norm for field in bind_fields):
        return []

    suggestions: list[LookupSuggestion] = []
    registry = get_entity_registry()

    for conflict_field in bind_fields:
        lookup_value = normalize_field_index_value(norm[conflict_field])
        other_lookup = {
            key: value for key, value in norm.items() if key != conflict_field
        }
        candidate_ids = registry.lookup_by_target_lookup(other_lookup)
        for entity_id in candidate_ids:
            entity = registry.lookup_by_id(entity_id)
            if entity is None:
                continue
            entity_value = normalize_field_index_value(
                entity.bind_value(conflict_field) or "",
            )
            if entity_value == lookup_value:
                continue
            suggested_lookup: dict[str, str] = {}
            for bind_field in bind_fields:
                raw = entity.bind_value(bind_field)
                if raw is not None and str(raw).strip():
                    suggested_lookup[bind_field] = str(raw).strip()
            if not suggested_lookup:
                continue
            suggestions.append(
                lookup_suggestion(
                    suggested_lookup=suggested_lookup,
                    id=entity.id,
                    score=1.0,
                    reason="same_bind_field_conflict",
                ),
            )
    return suggestions


def _lookup_suggestions_for_full_mvr(
    lookup: dict[str, str],
) -> list[LookupSuggestion]:
    conflicts = _same_bind_field_conflict_suggestions(lookup)
    if conflicts:
        return conflicts

    norm = normalized_lookup_values(lookup)
    name_value = norm.get("name")
    if name_value:
        return _rank_suggestions(name_value)
    return []


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
            norm = normalized_lookup_values(query.lookup)
            for field, value in norm.items():
                suggestions = _rank_bind_field_fuzzy_suggestions(field, value)
                if suggestions:
                    return TargetResolveResult(
                        kind="lookup_suggested",
                        entity_ids=[],
                        lookup_snapshot=dict(query.lookup),
                        suggestions=suggestions,
                    )

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

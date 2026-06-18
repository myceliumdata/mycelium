"""Step-1 target protocol resolve (MVR redesign M4/M7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agents.bind_alias_expansion import (
    AliasExpander,
    AliasExpansionResult,
    expand_field_aliases,
    load_network_guide_text,
)
from agents.entity_registry import EntityRegistry, get_entity_registry
from agents.field_index import normalize_field_index_value
from agents.entity_resolution import (
    _rank_bind_field_fuzzy_suggestions,
)
from models.state import DeliveryPayload, EntityQuery, LookupSuggestion, lookup_suggestion
from network.delivery import get_delivery_store, issue_delivery
from network.mvr import (
    default_record_type,
    infer_record_type_from_lookup,
    is_bootstrap_only_record_type,
    is_full_mvr_lookup,
    list_record_types,
    load_mvr,
    load_mvr_config,
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
    record_type: str | None = None


def _same_bind_field_conflict_suggestions(
    lookup: dict[str, str],
    *,
    record_type: str | None = None,
) -> list[LookupSuggestion]:
    norm = normalized_lookup_values(lookup)
    resolved_record_type = record_type or default_record_type()
    mvr = load_mvr(record_type=resolved_record_type)
    bind_fields = [f.strip().lower() for f in mvr.bind_fields if f.strip()]
    if len(bind_fields) < 2 or not all(field in norm for field in bind_fields):
        return []

    suggestions: list[LookupSuggestion] = []
    registry = get_entity_registry(record_type=resolved_record_type)

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
                    record_type=resolved_record_type,
                ),
            )
    return suggestions


def _lookup_suggestions_for_full_mvr(
    lookup: dict[str, str],
    *,
    record_type: str | None = None,
) -> list[LookupSuggestion]:
    resolved_record_type = record_type or default_record_type()
    conflicts = _same_bind_field_conflict_suggestions(
        lookup,
        record_type=resolved_record_type,
    )
    if conflicts:
        return conflicts

    norm = normalized_lookup_values(lookup)
    mvr = load_mvr(record_type=resolved_record_type)
    for bind_field in mvr.bind_fields:
        key = bind_field.strip().lower()
        if not key:
            continue
        value = norm.get(key)
        if value:
            suggestions = _rank_bind_field_fuzzy_suggestions(
                key,
                value,
                record_type=resolved_record_type,
            )
            if suggestions:
                return suggestions
    return []


def _try_bootstrap_only_alias_expansion(
    lookup: dict[str, str],
    *,
    record_type: str,
    registry: EntityRegistry,
    mvr: Any,
    alias_expander: AliasExpander | None = None,
) -> AliasExpansionResult:
    """Expand field aliases for lookup fields, retrying after each write batch."""
    guide_text = load_network_guide_text()
    norm = normalized_lookup_values(lookup)
    bind_fields = [field.strip().lower() for field in mvr.bind_fields if field.strip()]
    total_written = 0
    matched_ids: list[str] = []

    for field_key in bind_fields:
        if field_key not in norm:
            continue
        result = expand_field_aliases(
            record_type,
            field_key,
            norm[field_key],
            registry=registry,
            guide_text=guide_text,
            expander=alias_expander,
        )
        total_written += result.aliases_written
        if result.aliases_written:
            matched_ids = registry.lookup_by_target_lookup(lookup)
            if matched_ids:
                break

    return AliasExpansionResult(
        entity_ids=matched_ids,
        aliases_written=total_written,
    )


def _resolve_bootstrap_only_zero_hit(
    lookup: dict[str, str],
    *,
    record_type: str,
    registry: EntityRegistry,
    mvr: Any,
    alias_expander: AliasExpander | None = None,
) -> TargetResolveResult:
    """Bootstrap-only record types: lazy alias expansion, then suggest/not_found — never create."""
    expansion = _try_bootstrap_only_alias_expansion(
        lookup,
        record_type=record_type,
        registry=registry,
        mvr=mvr,
        alias_expander=alias_expander,
    )
    if expansion.entity_ids:
        return TargetResolveResult(
            kind="resolved",
            entity_ids=expansion.entity_ids,
            lookup_snapshot=dict(lookup),
            record_type=record_type,
        )

    suggestions = _lookup_suggestions_for_full_mvr(lookup, record_type=record_type)
    if suggestions:
        return TargetResolveResult(
            kind="lookup_suggested",
            entity_ids=[],
            lookup_snapshot=dict(lookup),
            suggestions=suggestions,
        )

    return TargetResolveResult(
        kind="not_found",
        entity_ids=[],
        lookup_snapshot=dict(lookup),
    )


def _resolve_single_record_type_step1(
    query: EntityQuery,
    *,
    record_type: str,
    alias_expander: AliasExpander | None = None,
) -> TargetResolveResult:
    """Resolve step-1 on one record type (single-type network or inferred type)."""
    registry = get_entity_registry(record_type=record_type)
    bootstrap_only = is_bootstrap_only_record_type(record_type)
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
            record_type=record_type,
        )

    if query.lookup:
        entity_ids = registry.lookup_by_target_lookup(query.lookup)
        if entity_ids:
            return TargetResolveResult(
                kind="resolved",
                entity_ids=entity_ids,
                lookup_snapshot=dict(query.lookup),
                record_type=record_type,
            )

        mvr = load_mvr(record_type=record_type)
        if not is_full_mvr_lookup(query.lookup, mvr):
            norm = normalized_lookup_values(query.lookup)
            for field, value in norm.items():
                suggestions = _rank_bind_field_fuzzy_suggestions(
                    field,
                    value,
                    record_type=record_type,
                )
                if suggestions:
                    return TargetResolveResult(
                        kind="lookup_suggested",
                        entity_ids=[],
                        lookup_snapshot=dict(query.lookup),
                        suggestions=suggestions,
                    )

            if bootstrap_only:
                return _resolve_bootstrap_only_zero_hit(
                    query.lookup,
                    record_type=record_type,
                    registry=registry,
                    mvr=mvr,
                    alias_expander=alias_expander,
                )

            missing = missing_mvr_bind_fields(query.lookup, mvr=mvr)
            return TargetResolveResult(
                kind="lookup_incomplete",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                required_fields=missing,
            )

        if query.confirm_new_entity:
            if bootstrap_only:
                return _resolve_bootstrap_only_zero_hit(
                    query.lookup,
                    record_type=record_type,
                    registry=registry,
                    mvr=mvr,
                    alias_expander=alias_expander,
                )
            return TargetResolveResult(
                kind="create_pending",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                create_on_deliver=True,
                record_type=record_type,
            )

        suggestions = _lookup_suggestions_for_full_mvr(query.lookup, record_type=record_type)
        if suggestions:
            return TargetResolveResult(
                kind="lookup_suggested",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                suggestions=suggestions,
            )

        if bootstrap_only:
            return _resolve_bootstrap_only_zero_hit(
                query.lookup,
                record_type=record_type,
                registry=registry,
                mvr=mvr,
                alias_expander=alias_expander,
            )

        return TargetResolveResult(
            kind="create_pending",
            entity_ids=[],
            lookup_snapshot=dict(query.lookup),
            create_on_deliver=True,
            record_type=record_type,
        )

    return TargetResolveResult(kind="not_found", entity_ids=[], lookup_snapshot={})


def resolve_id_all_record_types(entity_id: str) -> TargetResolveResult:
    """Search all record types for a uuid (no LLM)."""
    matching_record_types: list[str] = []
    for record_type in list_record_types():
        registry = get_entity_registry(record_type=record_type)
        if registry.lookup_by_id(entity_id) is not None:
            matching_record_types.append(record_type)
    if not matching_record_types:
        return TargetResolveResult(
            kind="not_found",
            entity_ids=[],
            lookup_snapshot={"id": entity_id},
        )
    if len(matching_record_types) > 1:
        return TargetResolveResult(
            kind="not_found",
            entity_ids=[],
            lookup_snapshot={"id": entity_id},
        )
    record_type = matching_record_types[0]
    return TargetResolveResult(
        kind="resolved",
        entity_ids=[entity_id],
        lookup_snapshot={"id": entity_id},
        record_type=record_type,
    )


def resolve_target_step1(
    query: EntityQuery,
    *,
    alias_expander: AliasExpander | None = None,
) -> TargetResolveResult:
    """Resolve step-1 target query by id or lookup AND (read-only)."""
    config = load_mvr_config()

    if len(config.record_types) == 1:
        return _resolve_single_record_type_step1(
            query,
            record_type=config.default_record_type,
            alias_expander=alias_expander,
        )

    entity_id = (query.id or "").strip()
    if entity_id:
        return resolve_id_all_record_types(entity_id)

    if query.lookup:
        inference = infer_record_type_from_lookup(query.lookup, config=config)
        if inference.kind == "resolved_record_type" and inference.record_type:
            return _resolve_single_record_type_step1(
                query,
                record_type=inference.record_type,
                alias_expander=alias_expander,
            )
        if inference.kind == "lookup_incomplete":
            if inference.record_type:
                return _resolve_single_record_type_step1(
                    query,
                    record_type=inference.record_type,
                    alias_expander=alias_expander,
                )
            return TargetResolveResult(
                kind="lookup_incomplete",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                required_fields=list(inference.required_fields),
                record_type=inference.record_type,
            )
        if inference.kind == "ambiguous":
            return TargetResolveResult(
                kind="lookup_incomplete",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                required_fields=[],
            )

    return TargetResolveResult(kind="not_found", entity_ids=[], lookup_snapshot={})


def issue_target_delivery(
    query: EntityQuery,
    entity_ids: list[str],
    *,
    create_on_deliver: bool = False,
    record_type: str | None = None,
) -> DeliveryPayload:
    """Issue and persist a delivery scope for a resolved step-1 query."""
    resolved_record_type = record_type or default_record_type()
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
        record_type=resolved_record_type,
    )
    get_delivery_store().put(scope)
    return DeliveryPayload.from_scope(scope)

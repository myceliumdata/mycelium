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
from agents.grain_disambiguation import GrainDisambiguator
from agents.entity_registry import EntityRegistry, get_entity_registry
from agents.field_index import normalize_field_index_value
from agents.entity_resolution import (
    _rank_bind_field_fuzzy_suggestions,
    _rank_suggestions,
)
from models.state import DeliveryPayload, EntityQuery, LookupSuggestion, lookup_suggestion
from network.delivery import get_delivery_store, issue_delivery
from network.mvr import (
    default_mvr_grain,
    is_closed_identity_grain,
    is_full_mvr_lookup,
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
    grain: str | None = None


def _same_bind_field_conflict_suggestions(
    lookup: dict[str, str],
    *,
    grain: str | None = None,
) -> list[LookupSuggestion]:
    norm = normalized_lookup_values(lookup)
    resolved_grain = grain or default_mvr_grain()
    mvr = load_mvr(grain=resolved_grain)
    bind_fields = [f.strip().lower() for f in mvr.bind_fields if f.strip()]
    if len(bind_fields) < 2 or not all(field in norm for field in bind_fields):
        return []

    suggestions: list[LookupSuggestion] = []
    registry = get_entity_registry(grain=resolved_grain)

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
                    grain=resolved_grain,
                ),
            )
    return suggestions


def _lookup_suggestions_for_full_mvr(
    lookup: dict[str, str],
    *,
    grain: str | None = None,
) -> list[LookupSuggestion]:
    resolved_grain = grain or default_mvr_grain()
    conflicts = _same_bind_field_conflict_suggestions(lookup, grain=resolved_grain)
    if conflicts:
        return conflicts

    norm = normalized_lookup_values(lookup)
    name_value = norm.get("name")
    if name_value:
        return _rank_suggestions(name_value)
    return []


def _try_closed_grain_alias_expansion(
    lookup: dict[str, str],
    *,
    grain: str,
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
            grain,
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


def _resolve_closed_grain_zero_hit(
    lookup: dict[str, str],
    *,
    grain: str,
    registry: EntityRegistry,
    mvr: Any,
    alias_expander: AliasExpander | None = None,
) -> TargetResolveResult:
    """Closed grains: lazy alias expansion, then suggest/not_found — never create."""
    expansion = _try_closed_grain_alias_expansion(
        lookup,
        grain=grain,
        registry=registry,
        mvr=mvr,
        alias_expander=alias_expander,
    )
    if expansion.entity_ids:
        return TargetResolveResult(
            kind="resolved",
            entity_ids=expansion.entity_ids,
            lookup_snapshot=dict(lookup),
            grain=grain,
        )

    suggestions = _lookup_suggestions_for_full_mvr(lookup, grain=grain)
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


def _resolve_single_grain_step1(
    query: EntityQuery,
    *,
    grain: str,
    alias_expander: AliasExpander | None = None,
) -> TargetResolveResult:
    """Resolve step-1 on one grain (CRM default path and explicit grain override)."""
    registry = get_entity_registry(grain=grain)
    closed_grain = is_closed_identity_grain(grain)
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
            grain=grain,
        )

    if query.lookup:
        entity_ids = registry.lookup_by_target_lookup(query.lookup)
        if entity_ids:
            return TargetResolveResult(
                kind="resolved",
                entity_ids=entity_ids,
                lookup_snapshot=dict(query.lookup),
                grain=grain,
            )

        mvr = load_mvr(grain=grain)
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
            if closed_grain:
                return _resolve_closed_grain_zero_hit(
                    query.lookup,
                    grain=grain,
                    registry=registry,
                    mvr=mvr,
                    alias_expander=alias_expander,
                )
            return TargetResolveResult(
                kind="create_pending",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                create_on_deliver=True,
                grain=grain,
            )

        suggestions = _lookup_suggestions_for_full_mvr(query.lookup, grain=grain)
        if suggestions:
            return TargetResolveResult(
                kind="lookup_suggested",
                entity_ids=[],
                lookup_snapshot=dict(query.lookup),
                suggestions=suggestions,
            )

        if closed_grain:
            return _resolve_closed_grain_zero_hit(
                query.lookup,
                grain=grain,
                registry=registry,
                mvr=mvr,
                alias_expander=alias_expander,
            )

        return TargetResolveResult(
            kind="create_pending",
            entity_ids=[],
            lookup_snapshot=dict(query.lookup),
            create_on_deliver=True,
            grain=grain,
        )

    return TargetResolveResult(kind="not_found", entity_ids=[], lookup_snapshot={})


def resolve_target_step1(
    query: EntityQuery,
    *,
    grain: str | None = None,
    alias_expander: AliasExpander | None = None,
    disambiguator: GrainDisambiguator | None = None,
) -> TargetResolveResult:
    """Resolve step-1 target query by id or lookup AND (read-only)."""
    config = load_mvr_config()
    explicit_grain = (query.grain or "").strip() or grain
    if explicit_grain:
        if explicit_grain not in config.grains:
            known = ", ".join(sorted(config.grains.keys()))
            raise ValueError(
                f"Unknown MVR grain {explicit_grain!r}; declared grains: {known}",
            )
        return _resolve_single_grain_step1(
            query,
            grain=explicit_grain,
            alias_expander=alias_expander,
        )

    if len(config.grains) == 1:
        return _resolve_single_grain_step1(
            query,
            grain=config.default_grain,
            alias_expander=alias_expander,
        )

    from agents.query_grain_router import resolve_id_all_grains, resolve_lookup_multi_grain

    entity_id = (query.id or "").strip()
    if entity_id:
        return resolve_id_all_grains(entity_id)

    if query.lookup:
        return resolve_lookup_multi_grain(
            query,
            alias_expander=alias_expander,
            disambiguator=disambiguator,
        )

    return TargetResolveResult(kind="not_found", entity_ids=[], lookup_snapshot={})


def issue_target_delivery(
    query: EntityQuery,
    entity_ids: list[str],
    *,
    create_on_deliver: bool = False,
    grain: str | None = None,
) -> DeliveryPayload:
    """Issue and persist a delivery scope for a resolved step-1 query."""
    resolved_grain = grain or default_mvr_grain()
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
        grain=resolved_grain,
    )
    get_delivery_store().put(scope)
    return DeliveryPayload.from_scope(scope)

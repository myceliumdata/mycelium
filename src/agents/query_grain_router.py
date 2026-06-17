"""Multi-grain fan-out lookup and disambiguation for step-1 target resolve."""

from __future__ import annotations

from typing import Any

from agents.bind_alias_expansion import AliasExpander
from agents.entity_registry import get_entity_registry
from agents.grain_disambiguation import (
    GrainDisambiguator,
    disambiguate_grain_hits,
)
from agents.target_resolve import (
    TargetResolveResult,
    _resolve_closed_grain_zero_hit,
    _resolve_single_grain_step1,
    _try_closed_grain_alias_expansion,
)
from models.state import EntityQuery, LookupSuggestion, lookup_suggestion
from network.mvr import (
    default_mvr_grain,
    is_closed_identity_grain,
    is_full_mvr_lookup,
    list_mvr_grains,
    load_mvr,
    missing_mvr_bind_fields,
    normalized_lookup_values,
)


def filter_lookup_for_grain(
    lookup: dict[str, str],
    bind_fields: list[str],
) -> dict[str, str]:
    """Return lookup keys that apply to a grain's MVR bind fields."""
    allowed = {field.strip().lower() for field in bind_fields if field.strip()}
    norm = normalized_lookup_values(lookup)
    return {key: value for key, value in norm.items() if key in allowed}


def fan_out_lookup(lookup: dict[str, str]) -> dict[str, list[str]]:
    """Fan-out AND lookup per declared grain (skip grains with empty filtered map)."""
    hits: dict[str, list[str]] = {}
    for grain in list_mvr_grains():
        mvr = load_mvr(grain=grain)
        filtered = filter_lookup_for_grain(lookup, mvr.bind_fields)
        if not filtered:
            continue
        registry = get_entity_registry(grain=grain)
        entity_ids = registry.lookup_by_target_lookup(filtered)
        if entity_ids:
            hits[grain] = entity_ids
    return hits


def grains_with_filtered_lookup(lookup: dict[str, str]) -> dict[str, dict[str, str]]:
    """Map each grain to its non-empty filtered lookup (participating grains)."""
    participated: dict[str, dict[str, str]] = {}
    for grain in list_mvr_grains():
        mvr = load_mvr(grain=grain)
        filtered = filter_lookup_for_grain(lookup, mvr.bind_fields)
        if filtered:
            participated[grain] = filtered
    return participated


def resolve_id_all_grains(entity_id: str) -> TargetResolveResult:
    """Search all grains for a uuid (no LLM)."""
    matching_grains: list[str] = []
    for grain in list_mvr_grains():
        registry = get_entity_registry(grain=grain)
        if registry.lookup_by_id(entity_id) is not None:
            matching_grains.append(grain)
    if not matching_grains:
        return TargetResolveResult(
            kind="not_found",
            entity_ids=[],
            lookup_snapshot={"id": entity_id},
        )
    if len(matching_grains) > 1:
        return TargetResolveResult(
            kind="not_found",
            entity_ids=[],
            lookup_snapshot={"id": entity_id},
        )
    grain = matching_grains[0]
    return TargetResolveResult(
        kind="resolved",
        entity_ids=[entity_id],
        lookup_snapshot={"id": entity_id},
        grain=grain,
    )


def _result_from_grain_hits(
    hits_by_grain: dict[str, list[str]],
    lookup_snapshot: dict[str, Any],
    *,
    disambiguator: GrainDisambiguator | None = None,
) -> TargetResolveResult:
    grains_with_hits = [grain for grain, ids in hits_by_grain.items() if ids]
    if not grains_with_hits:
        return TargetResolveResult(
            kind="not_found",
            entity_ids=[],
            lookup_snapshot=lookup_snapshot,
        )

    if len(grains_with_hits) == 1:
        grain = grains_with_hits[0]
        return TargetResolveResult(
            kind="resolved",
            entity_ids=list(hits_by_grain[grain]),
            lookup_snapshot=lookup_snapshot,
            grain=grain,
        )

    hit_rows: list[tuple[str, str, Any]] = []
    for grain in grains_with_hits:
        registry = get_entity_registry(grain=grain)
        for entity_id in hits_by_grain[grain]:
            entity = registry.lookup_by_id(entity_id)
            if entity is not None:
                hit_rows.append((grain, entity_id, entity))

    choice = disambiguate_grain_hits(hit_rows, disambiguator=disambiguator)
    if choice.kind == "chosen" and choice.grain and choice.entity_id:
        return TargetResolveResult(
            kind="resolved",
            entity_ids=[choice.entity_id],
            lookup_snapshot=lookup_snapshot,
            grain=choice.grain,
        )
    if choice.kind == "chosen_grain" and choice.grain:
        return TargetResolveResult(
            kind="resolved",
            entity_ids=list(hits_by_grain.get(choice.grain, [])),
            lookup_snapshot=lookup_snapshot,
            grain=choice.grain,
        )

    suggestions: list[LookupSuggestion] = []
    for grain, entity_id, entity in hit_rows:
        mvr = load_mvr(grain=grain)
        suggested_lookup: dict[str, str] = {}
        for field in mvr.bind_fields:
            key = field.strip().lower()
            if not key:
                continue
            raw = entity.bind_value(key)
            if raw is not None and str(raw).strip():
                suggested_lookup[key] = str(raw).strip()
        if not suggested_lookup:
            continue
        suggestions.append(
            lookup_suggestion(
                suggested_lookup=suggested_lookup,
                id=entity_id,
                score=1.0,
                reason="cross_grain_ambiguous",
                grain=grain,
            ),
        )
    return TargetResolveResult(
        kind="lookup_suggested",
        entity_ids=[],
        lookup_snapshot=lookup_snapshot,
        suggestions=suggestions,
    )


def _partial_lookup_result(
    lookup: dict[str, str],
    participated: dict[str, dict[str, str]],
) -> TargetResolveResult | None:
    from agents.entity_resolution import _rank_bind_field_fuzzy_suggestions

    for grain, filtered in participated.items():
        mvr = load_mvr(grain=grain)
        if is_full_mvr_lookup(filtered, mvr):
            continue
        norm = normalized_lookup_values(filtered)
        for field, value in norm.items():
            suggestions = _rank_bind_field_fuzzy_suggestions(field, value, grain=grain)
            if suggestions:
                return TargetResolveResult(
                    kind="lookup_suggested",
                    entity_ids=[],
                    lookup_snapshot=dict(lookup),
                    suggestions=suggestions,
                )
        if len(participated) == 1:
            missing = missing_mvr_bind_fields(filtered, mvr=mvr)
            return TargetResolveResult(
                kind="lookup_incomplete",
                entity_ids=[],
                lookup_snapshot=dict(lookup),
                required_fields=missing,
            )
    return None


def _all_participating_closed(participated: dict[str, dict[str, str]]) -> bool:
    return all(is_closed_identity_grain(grain) for grain in participated)


def resolve_lookup_multi_grain(
    query: EntityQuery,
    *,
    alias_expander: AliasExpander | None = None,
    disambiguator: GrainDisambiguator | None = None,
) -> TargetResolveResult:
    """Fan-out lookup across grains with 0-hit alias retry and disambiguation."""
    lookup = dict(query.lookup)
    lookup_snapshot = dict(lookup)
    participated = grains_with_filtered_lookup(lookup)
    if not participated:
        return TargetResolveResult(
            kind="not_found",
            entity_ids=[],
            lookup_snapshot=lookup_snapshot,
        )

    hits = fan_out_lookup(lookup)
    if hits:
        return _result_from_grain_hits(
            hits,
            lookup_snapshot,
            disambiguator=disambiguator,
        )

    partial = _partial_lookup_result(lookup, participated)
    if partial is not None:
        return partial

    for grain, filtered in participated.items():
        if not is_closed_identity_grain(grain):
            continue
        registry = get_entity_registry(grain=grain)
        mvr = load_mvr(grain=grain)
        _try_closed_grain_alias_expansion(
            filtered,
            grain=grain,
            registry=registry,
            mvr=mvr,
            alias_expander=alias_expander,
        )

    hits = fan_out_lookup(lookup)
    if hits:
        return _result_from_grain_hits(
            hits,
            lookup_snapshot,
            disambiguator=disambiguator,
        )

    if _all_participating_closed(participated):
        grain = default_mvr_grain()
        registry = get_entity_registry(grain=grain)
        mvr = load_mvr(grain=grain)
        filtered = participated.get(grain, participated[next(iter(participated))])
        return _resolve_closed_grain_zero_hit(
            filtered,
            grain=grain,
            registry=registry,
            mvr=mvr,
            alias_expander=alias_expander,
        )

    return _resolve_single_grain_step1(
        query,
        grain=default_mvr_grain(),
        alias_expander=alias_expander,
    )

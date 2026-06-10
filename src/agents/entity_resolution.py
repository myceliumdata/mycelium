"""Entity resolution: registry, near-miss suggestions, and bind negotiation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Literal

from agents.entity_registry import get_entity_registry, registry_entity_to_match
from models.state import EntityKeySuggestion, EntityQuery
from network.mvr import load_mvr, normalize_binding

SUGGESTION_MIN_SCORE = 0.85
SUGGESTION_MAX_COUNT = 5

EntityResolutionKind = Literal[
    "exact",
    "multiple",
    "suggest",
    "unknown",
    "under_specified",
    "bind_provisional",
    "none",
]


@dataclass
class EntityResolution:
    kind: EntityResolutionKind
    matches: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[EntityKeySuggestion] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=list)
    duplicate_bind: bool = False


def normalize_name_for_comparison(name: str) -> str:
    """Normalize a display name for fuzzy comparison only (never rewrite caller keys)."""
    text = name.strip().lower()
    for ch in ("'", "-", "\u2019"):
        text = text.replace(ch, "")
    return " ".join(text.split())


def _first_token(normalized: str) -> str:
    parts = normalized.split()
    return parts[0] if parts else ""


def _is_uuid_shaped(key: str) -> bool:
    try:
        uuid.UUID(key)
    except ValueError:
        return False
    return True


def is_provisional_registry_match(record: dict[str, Any]) -> bool:
    """True when the match row is a provisional registry entity."""
    return (
        record.get("_registry") is True
        and record.get("_validation_state") == "provisional"
    )


def lookup_entities_by_key(entity_key: str) -> list[dict[str, Any]]:
    """Resolve by registry UUID or exact name (case-insensitive).

    UUID match returns zero or one record. Name match may return multiple
    records when the same name appears with different employers.
    """
    key = entity_key.strip()
    if not key:
        return []

    registry = get_entity_registry()
    if _is_uuid_shaped(key):
        by_id = registry.lookup_by_id(key)
        if by_id is not None:
            return [registry_entity_to_match(by_id)]
        return []

    by_name = registry.lookup_by_name(key)
    return [registry_entity_to_match(entity) for entity in by_name]


def _rank_suggestions(entity_key: str) -> list[EntityKeySuggestion]:
    query_norm = normalize_name_for_comparison(entity_key)
    if not query_norm:
        return []

    query_first = _first_token(query_norm)
    candidates: list[EntityKeySuggestion] = []

    for entity in get_entity_registry().list_entities():
        name = entity.name or ""
        candidate_norm = normalize_name_for_comparison(name)
        if not candidate_norm:
            continue
        if _first_token(candidate_norm) != query_first:
            continue
        score = SequenceMatcher(None, query_norm, candidate_norm).ratio()
        if score < SUGGESTION_MIN_SCORE:
            continue
        candidates.append(
            EntityKeySuggestion(
                entity_key=name,
                id=entity.id,
                name=name,
                employer=entity.employer,
                score=round(score, 4),
                reason="sequence_ratio",
            ),
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:SUGGESTION_MAX_COUNT]


def resolve_entity(query: EntityQuery) -> EntityResolution:
    """Unified resolution: registry → suggest → unknown / under_specified / bind."""
    key = query.entity_key.strip()
    if not key:
        return EntityResolution(kind="none")

    registry = get_entity_registry()
    mvr = load_mvr()
    binding = normalize_binding(query.binding, mvr)
    employer = binding.get("employer")

    if employer:
        bound = registry.lookup_by_bind_key(key, employer)
        if bound is not None:
            return EntityResolution(
                kind="exact",
                matches=[registry_entity_to_match(bound)],
                duplicate_bind=bool(query.binding),
            )

    if _is_uuid_shaped(key):
        by_id = registry.lookup_by_id(key)
        if by_id is not None:
            return EntityResolution(
                kind="exact",
                matches=[registry_entity_to_match(by_id)],
            )

    if not _is_uuid_shaped(key) and not employer:
        by_name = registry.lookup_by_name(key)
        if len(by_name) == 1:
            return EntityResolution(
                kind="exact",
                matches=[registry_entity_to_match(by_name[0])],
            )
        if len(by_name) >= 2:
            matches = [registry_entity_to_match(entity) for entity in by_name]
            if not query.binding and all(
                entity.source == "seed_bootstrap" for entity in by_name
            ):
                return EntityResolution(kind="multiple", matches=matches)
            required = mvr.required_bind_fields(key, binding)
            if query.binding:
                return EntityResolution(
                    kind="under_specified",
                    required_fields=required or ["employer"],
                )
            return EntityResolution(
                kind="unknown",
                required_fields=required or ["employer"],
            )

    if _is_uuid_shaped(key):
        return EntityResolution(kind="none")

    if not employer:
        suggestions = _rank_suggestions(key)
        if suggestions:
            return EntityResolution(kind="suggest", suggestions=suggestions)

    required = mvr.required_bind_fields(key, binding)
    if required:
        if query.binding:
            return EntityResolution(
                kind="under_specified",
                required_fields=required,
            )
        return EntityResolution(kind="unknown", required_fields=required)

    entity, is_duplicate = registry.bind_provisional(key, employer or "")
    match = registry_entity_to_match(entity)
    if is_duplicate:
        return EntityResolution(
            kind="exact",
            matches=[match],
            duplicate_bind=True,
        )
    return EntityResolution(kind="bind_provisional", matches=[match])


def resolve_entity_key(entity_key: str) -> EntityResolution:
    """Resolve by entity_key only (no binding); used in unit tests."""
    return resolve_entity(EntityQuery(entity_key=entity_key))


def resolve_entity_for_lookup(entity_key: str) -> EntityResolution:
    """Read-only resolution for admin/CLI status (never creates provisional binds)."""
    key = entity_key.strip()
    if not key:
        return EntityResolution(kind="none")

    registry = get_entity_registry()
    mvr = load_mvr()

    if _is_uuid_shaped(key):
        by_id = registry.lookup_by_id(key)
        if by_id is not None:
            return EntityResolution(
                kind="exact",
                matches=[registry_entity_to_match(by_id)],
            )
        return EntityResolution(kind="none")

    by_name = registry.lookup_by_name(key)
    if len(by_name) == 1:
        return EntityResolution(
            kind="exact",
            matches=[registry_entity_to_match(by_name[0])],
        )
    if len(by_name) >= 2:
        matches = [registry_entity_to_match(entity) for entity in by_name]
        if all(entity.source == "seed_bootstrap" for entity in by_name):
            return EntityResolution(kind="multiple", matches=matches)
        required = mvr.required_bind_fields(key, {})
        return EntityResolution(
            kind="unknown",
            required_fields=required or ["employer"],
        )

    suggestions = _rank_suggestions(key)
    if suggestions:
        return EntityResolution(kind="suggest", suggestions=suggestions)

    required = mvr.required_bind_fields(key, {})
    if required:
        return EntityResolution(kind="unknown", required_fields=required)

    return EntityResolution(
        kind="unknown",
        required_fields=mvr.required_fields_for_entity_key(key),
    )

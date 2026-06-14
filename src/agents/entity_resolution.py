"""Entity resolution: near-miss suggestions and read-only status lookup."""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Literal

from agents.entity_registry import get_entity_registry, registry_entity_to_match
from agents.field_index import normalize_field_index_value
from models.state import LookupSuggestion, lookup_suggestion
from network.mvr import normalized_lookup_values

SUGGESTION_MIN_SCORE = 0.85
SUGGESTION_MAX_COUNT = 5

EntityResolutionKind = Literal[
    "exact",
    "multiple",
    "none",
]


@dataclass
class EntityResolution:
    kind: EntityResolutionKind
    matches: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[LookupSuggestion] = field(default_factory=list)
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


def is_provisional_registry_match(record: dict[str, Any]) -> bool:
    """True when the match row is a provisional registry entity."""
    return (
        record.get("_registry") is True
        and record.get("_validation_state") == "provisional"
    )


def _rank_suggestions(entity_key: str) -> list[LookupSuggestion]:
    query_norm = normalize_name_for_comparison(entity_key)
    if not query_norm:
        return []

    query_first = _first_token(query_norm)
    candidates: list[LookupSuggestion] = []

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
            lookup_suggestion(
                suggested_lookup={"name": name},
                id=entity.id,
                name=name,
                employer=entity.employer,
                score=score,
                reason="sequence_ratio",
            ),
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:SUGGESTION_MAX_COUNT]


def _rank_employer_suggestions(employer: str) -> list[LookupSuggestion]:
    query_norm = normalize_field_index_value(employer)
    if not query_norm:
        return []

    canonical_by_norm: dict[str, str] = {}
    for entity in get_entity_registry().list_entities():
        raw_employer = entity.employer
        if raw_employer is None or not str(raw_employer).strip():
            continue
        canonical = str(raw_employer)
        candidate_norm = normalize_field_index_value(canonical)
        if not candidate_norm or candidate_norm in canonical_by_norm:
            continue
        canonical_by_norm[candidate_norm] = canonical

    candidates: list[LookupSuggestion] = []
    for candidate_norm, canonical_employer in canonical_by_norm.items():
        score = SequenceMatcher(None, query_norm, candidate_norm).ratio()
        if score < SUGGESTION_MIN_SCORE:
            continue
        candidates.append(
            lookup_suggestion(
                suggested_lookup={"employer": canonical_employer},
                employer=canonical_employer,
                score=score,
                reason="employer_sequence_ratio",
            ),
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:SUGGESTION_MAX_COUNT]


def resolve_status_for_target_lookup(lookup: dict[str, str]) -> EntityResolution:
    """Read-only MVR AND lookup for admin status (never creates or runs graph)."""
    normalized = normalized_lookup_values(lookup)
    if not normalized:
        return EntityResolution(kind="none")

    registry = get_entity_registry()
    entity_ids = registry.lookup_by_target_lookup(normalized)
    matches: list[dict[str, Any]] = []
    for entity_id in entity_ids:
        entity = registry.lookup_by_id(entity_id)
        if entity is not None:
            matches.append(registry_entity_to_match(entity))

    if len(matches) == 1:
        return EntityResolution(kind="exact", matches=matches)
    if len(matches) >= 2:
        return EntityResolution(kind="multiple", matches=matches)
    return EntityResolution(kind="none")

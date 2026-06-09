"""Entity key resolution: exact match, ambiguity, and near-miss suggestions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Literal

from agents.seed import find_by_key, get_seed_data
from models.state import EntityKeySuggestion

SUGGESTION_MIN_SCORE = 0.85
SUGGESTION_MAX_COUNT = 5

EntityResolutionKind = Literal["exact", "multiple", "suggest", "unknown", "none"]


@dataclass
class EntityResolution:
    kind: EntityResolutionKind
    matches: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[EntityKeySuggestion] = field(default_factory=list)


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


def _rank_suggestions(entity_key: str) -> list[EntityKeySuggestion]:
    query_norm = normalize_name_for_comparison(entity_key)
    if not query_norm:
        return []

    query_first = _first_token(query_norm)
    candidates: list[EntityKeySuggestion] = []

    for person in get_seed_data().people:
        name = person.get("name") or ""
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
                id=person.get("id", ""),
                name=name,
                employer=person.get("employer"),
                score=round(score, 4),
                reason="sequence_ratio",
            ),
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:SUGGESTION_MAX_COUNT]


def resolve_entity_key(entity_key: str) -> EntityResolution:
    """Resolve an entity key to exact matches, ambiguity, suggestions, or none."""
    key = entity_key.strip()
    if not key:
        return EntityResolution(kind="none")

    matches = find_by_key(key)
    if matches:
        kind: EntityResolutionKind = "multiple" if len(matches) > 1 else "exact"
        return EntityResolution(kind=kind, matches=matches)

    if _is_uuid_shaped(key):
        return EntityResolution(kind="none")

    suggestions = _rank_suggestions(key)
    if suggestions:
        return EntityResolution(kind="suggest", suggestions=suggestions)

    return EntityResolution(kind="unknown")

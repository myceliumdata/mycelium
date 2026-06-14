"""Test helpers for registry lookups (target protocol)."""

from __future__ import annotations

from typing import Any

from agents.entity_registry import get_entity_registry, registry_entity_to_match


def lookup_entities_by_name(name: str) -> list[dict[str, Any]]:
    """Resolve seed/registry rows by exact normalized name (test fixtures)."""
    registry = get_entity_registry()
    return [
        registry_entity_to_match(entity)
        for entity in registry.lookup_by_field("name", name)
    ]

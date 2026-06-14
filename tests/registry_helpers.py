"""Test helpers for registry lookups and target-protocol query flows."""

from __future__ import annotations

from typing import Any

from agents.entity_registry import get_entity_registry, registry_entity_to_match
from graphs.core import run_query
from models.state import EntityQuery, QueryResponse


def lookup_entities_by_name(name: str) -> list[dict[str, Any]]:
    """Resolve seed/registry rows by exact normalized name (test fixtures)."""
    registry = get_entity_registry()
    return [
        registry_entity_to_match(entity)
        for entity in registry.lookup_by_field("name", name)
    ]


def step1_resolve(
    *,
    lookup: dict[str, str] | None = None,
    entity_id: str | None = None,
    requested_attributes: list[str] | None = None,
    confirm_new_entity: bool = False,
    provenance: bool = False,
    thread_id: str | None = None,
) -> QueryResponse:
    """Run step-1 target resolve."""
    return run_query(
        EntityQuery(
            id=entity_id,
            lookup=lookup or {},
            requested_attributes=requested_attributes or [],
            confirm_new_entity=confirm_new_entity,
            provenance=provenance,
        ),
        thread_id=thread_id,
    )


def step2_deliver(
    delivery_id: str,
    *,
    requested_attributes: list[str] | None = None,
    quote_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Run step-2 deliver for a prior delivery scope."""
    return run_query(
        EntityQuery(
            delivery_id=delivery_id,
            quote_id=quote_id,
        ),
        thread_id=thread_id,
    )


def resolve_and_deliver(
    *,
    lookup: dict[str, str] | None = None,
    entity_id: str | None = None,
    requested_attributes: list[str] | None = None,
    quote_id: str | None = None,
    confirm_new_entity: bool = False,
    thread_id: str | None = None,
) -> tuple[QueryResponse, QueryResponse]:
    """Step 1 lookup_resolved then step 2 deliver (attrs quoted on step 1)."""
    first = step1_resolve(
        lookup=lookup,
        entity_id=entity_id,
        requested_attributes=requested_attributes,
        confirm_new_entity=confirm_new_entity,
        thread_id=thread_id,
    )
    assert first.outcome == "lookup_resolved", first.message
    assert first.delivery is not None
    second = step2_deliver(
        first.delivery.delivery_id,
        quote_id=quote_id,
        thread_id=thread_id,
    )
    return first, second

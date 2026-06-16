"""Shared specialist I/O helpers — internal to specialists package; use SpecialistAgent."""

from __future__ import annotations

from typing import Any

from agents.specialists.agent import SpecialistAgent


def _agent(category: str, specialist_name: str) -> SpecialistAgent:
    from agents.registry import get_agent_registry

    return get_agent_registry().get_agent_instance(specialist_name)


def write_fields(
    category: str,
    specialist_name: str,
    entity_id: str,
    fields: dict[str, str],
    *,
    actor_kind: str,
    at: str | None = None,
) -> dict[str, str]:
    return _agent(category, specialist_name).write_fields(
        entity_id,
        fields,
        actor_kind=actor_kind,
        at=at,
    )


def read_fields(
    category: str,
    specialist_name: str,
    entity_id: str,
    fields: list[str],
    *,
    include_versions: bool = False,
    include_provenance: bool | None = None,
) -> dict[str, Any]:
    return _agent(category, specialist_name).read_fields(
        entity_id,
        fields,
        include_versions=include_versions,
        include_provenance=include_provenance,
    )


def bootstrap_entity(
    category: str,
    specialist_name: str,
    entity_id: str,
    fields: dict[str, str],
    *,
    actor_kind: str = "seed_bootstrap",
) -> dict[str, str]:
    return _agent(category, specialist_name).bootstrap_entity(
        entity_id,
        fields,
        actor_kind=actor_kind,
    )


def analyze_category_storage(category: str) -> dict[str, Any]:
    return SpecialistAgent(category=category).analyze_storage()


def read_category_slice(
    category: str,
    entity_ids: list[str],
    *,
    bind_fields: frozenset[str] | set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    return SpecialistAgent(category=category).read_category_slice(
        entity_ids,
        bind_fields=bind_fields,
    )


def entity_field_statuses_for_category(
    category: str,
    specialist_name: str,
    entity_id: str,
) -> list[dict[str, Any]]:
    return _agent(category, specialist_name).entity_field_statuses(entity_id)


def ensure_category_storage(category: str) -> None:
    SpecialistAgent(category=category).ensure_storage()

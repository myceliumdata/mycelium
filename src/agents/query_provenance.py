"""Build structured provenance for QueryResponse when EntityQuery.provenance=true."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from agents.classification import get_category_tree
from agents.entity_registry import get_entity_registry
from agents.registry import get_agent_registry
from agents.specialists.protocol import dispatch_read_fields
from models.state import EntityQuery, QueryResponse, normalized_requested_attributes
from network.intent_map import load_intent_map, lookup_intent_slug
from network.paths import NetworkPaths, resolve_network_root


def _category_for_attribute(attr: str, *, entity_id: str) -> str | None:
    registry = get_entity_registry()
    entity = registry.lookup_by_id(entity_id)
    if entity is not None:
        source = entity.attr_sources.get(attr)
        if source:
            return str(source)
    return get_category_tree().mapped_category(attr)


def _agent_for_category(category: str) -> str | None:
    categories = get_category_tree().get_categories()
    cat = categories.get(category)
    if cat is not None and cat.assigned_agent:
        return cat.assigned_agent
    registry = get_agent_registry()
    for agent in registry.list_agents():
        if agent.get("category") == category:
            name = agent.get("name")
            return str(name) if name else None
    return None


def _candidate_storage_keys(
    attr: str,
    query_scope: dict[str, str] | None,
) -> list[str]:
    key = attr.strip().lower()
    if not query_scope:
        return [key]
    year = str(query_scope.get("yearID") or "").strip()
    if year:
        return [f"{key}::{year}", key]
    return [key]


def _read_attribute_provenance(
    agent_name: str,
    entity_id: str,
    attr: str,
    *,
    intent_map: dict[str, str],
    query_scope: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    key = attr.strip().lower()
    for storage_key in _candidate_storage_keys(attr, query_scope):
        read = dispatch_read_fields(agent_name, entity_id, [storage_key], include_versions=True)
        entry = read.get(storage_key)
        if isinstance(entry, dict):
            provenance = entry.get("provenance")
            if isinstance(provenance, dict) and provenance.get("versions"):
                result = deepcopy(provenance)
                if storage_key != key:
                    for version in result.get("versions", []):
                        if isinstance(version, dict) and isinstance(version.get("parameters"), dict):
                            version["parameters"] = {
                                **version["parameters"],
                                "attribute": key,
                            }
                return result

    slug = lookup_intent_slug(key, intent_map)
    if slug and slug != key:
        slug_read = dispatch_read_fields(agent_name, entity_id, [slug], include_versions=True)
        slug_entry = slug_read.get(slug)
        if isinstance(slug_entry, dict):
            provenance = slug_entry.get("provenance")
            if isinstance(provenance, dict) and provenance.get("versions"):
                adjusted = deepcopy(provenance)
                for version in adjusted.get("versions", []):
                    if isinstance(version, dict) and isinstance(version.get("parameters"), dict):
                        version["parameters"] = {
                            **version["parameters"],
                            "attribute": key,
                            "intent_slug": slug,
                        }
                return adjusted
    return None


def build_query_provenance(
    *,
    entity_ids: list[str],
    requested_attributes: list[str],
    paths: Any | None = None,
    query_scope: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Return provenance payload or None when nothing to attach."""
    _ = paths
    requested = normalized_requested_attributes(requested_attributes)
    if not requested or not entity_ids:
        return None

    try:
        intent_map = load_intent_map(NetworkPaths.from_root(resolve_network_root()))
    except (ValueError, OSError):
        intent_map = {}

    entities: list[dict[str, Any]] = []

    for entity_id in entity_ids:
        if not entity_id:
            continue
        attributes: dict[str, Any] = {}
        for attr in requested:
            category = _category_for_attribute(attr, entity_id=entity_id)
            if not category:
                continue
            agent_name = _agent_for_category(category)
            if not agent_name:
                continue
            provenance = _read_attribute_provenance(
                agent_name,
                entity_id,
                attr,
                intent_map=intent_map,
                query_scope=query_scope,
            )
            if provenance is not None:
                attributes[attr] = provenance
        if attributes:
            entities.append({"id": entity_id, "attributes": attributes})

    if not entities:
        return None
    return {"entities": entities}


def apply_query_provenance(
    response: QueryResponse,
    query: EntityQuery,
    matched_records: list[dict[str, Any]],
    *,
    requested_attributes: list[str] | None = None,
    provenance: bool | None = None,
    query_scope: dict[str, str] | None = None,
) -> QueryResponse:
    """Attach QueryResponse.provenance when the request flag is set."""
    provenance_flag = query.provenance if provenance is None else provenance
    if not provenance_flag:
        return response
    if response.outcome not in {"assembled", "found"}:
        return response
    attrs = (
        normalized_requested_attributes(requested_attributes)
        if requested_attributes is not None
        else normalized_requested_attributes(query.requested_attributes)
    )
    if not attrs:
        return response

    entity_ids = [
        str(record["id"])
        for record in matched_records
        if isinstance(record, dict) and record.get("id")
    ]
    provenance_payload = build_query_provenance(
        entity_ids=entity_ids,
        requested_attributes=attrs,
        query_scope=query_scope,
    )
    if provenance_payload is None:
        return response
    return response.model_copy(update={"provenance": provenance_payload})

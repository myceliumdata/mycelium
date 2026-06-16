"""Build structured provenance for QueryResponse when EntityQuery.provenance=true."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from agents.classification import get_category_tree
from agents.entity_registry import get_entity_registry
from agents.registry import get_agent_registry
from agents.specialists.protocol import dispatch_read_fields
from models.state import EntityQuery, QueryResponse, normalized_requested_attributes


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


def build_query_provenance(
    *,
    entity_ids: list[str],
    requested_attributes: list[str],
    paths: Any | None = None,
) -> dict[str, Any] | None:
    """Return provenance payload or None when nothing to attach."""
    _ = paths
    requested = normalized_requested_attributes(requested_attributes)
    if not requested or not entity_ids:
        return None

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
            read = dispatch_read_fields(
                agent_name,
                entity_id,
                [attr],
                include_versions=True,
            )
            entry = read.get(attr.strip().lower())
            if isinstance(entry, dict):
                provenance = entry.get("provenance")
                if isinstance(provenance, dict) and provenance.get("versions"):
                    attributes[attr] = deepcopy(provenance)
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
    )
    if provenance_payload is None:
        return response
    return response.model_copy(update={"provenance": provenance_payload})

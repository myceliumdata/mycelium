"""Build structured provenance for QueryResponse when EntityQuery.provenance=true."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any

from agents.classification import get_category_tree
from agents.entity_registry import get_entity_registry
from agents.specialist_fields import (
    is_versioned_field,
    storage_record,
    validate_versioned_field,
)
from models.state import EntityQuery, QueryResponse, normalized_requested_attributes
from network.paths import NetworkPaths, resolve_network_root, runtime_path


def _category_for_attribute(attr: str, *, entity_id: str) -> str | None:
    registry = get_entity_registry()
    entity = registry.lookup_by_id(entity_id)
    if entity is not None:
        source = entity.attr_sources.get(attr)
        if source:
            return str(source)
    return get_category_tree().mapped_category(attr)


def _runtime_paths(paths: NetworkPaths | None) -> NetworkPaths:
    if paths is not None:
        return paths
    base = NetworkPaths.from_root(resolve_network_root())
    return replace(base, agents_dir=runtime_path("MYCELIUM_AGENT_DATA_DIR"))


def _provenance_field_entry(entry: Any, *, field_name: str, category: str) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    validate_versioned_field(entry, field_name=field_name, category=category)
    if not is_versioned_field(entry):
        return None
    versions = entry.get("versions") or []
    if not versions:
        return None
    return {
        "current_version_id": entry.get("current_version_id"),
        "versions": deepcopy(versions),
    }


def build_query_provenance(
    *,
    entity_ids: list[str],
    requested_attributes: list[str],
    paths: NetworkPaths | None = None,
) -> dict[str, Any] | None:
    """Return provenance payload or None when nothing to attach."""
    requested = normalized_requested_attributes(requested_attributes)
    if not requested or not entity_ids:
        return None

    resolved_paths = _runtime_paths(paths)
    entities: list[dict[str, Any]] = []

    for entity_id in entity_ids:
        if not entity_id:
            continue
        attributes: dict[str, Any] = {}
        for attr in requested:
            category = _category_for_attribute(attr, entity_id=entity_id)
            if not category:
                continue
            record = storage_record(resolved_paths.agents_dir, category, entity_id)
            entry = record.get(attr)
            field_provenance = _provenance_field_entry(
                entry,
                field_name=attr,
                category=category,
            )
            if field_provenance is not None:
                attributes[attr] = field_provenance
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

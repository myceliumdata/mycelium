"""Shared graph helpers for baseball product specialists (roster, franchise)."""

from __future__ import annotations

import json
from typing import Any, Callable

from agents.registry_bridge import entity_source_key
from agents.responses import response_found, response_non_core, response_not_found
from agents.specialists.agent import SpecialistAgent
from agents.specialists.fields import field_display_value, field_has_value, field_is_na
from models.state import MyceliumGraphState
from network.dataset_source import load_pack_dataset_source
from network.paths import NetworkPaths, resolve_network_root
from network.warehouse import default_warehouse_path, query_warehouse

from pack_common import (
    coerce_state,
    identity_from_context,
    now_iso,
    overall_field_status,
    query_year_id,
    resolve_entity_id,
    resolve_owned_fields,
)

LAHMAN_TEAM_ID = "lahman.teamID"


def _scoped_storage_key(
    key: str,
    year_id: str | None,
    *,
    scope_sensitive: bool,
) -> str:
    if scope_sensitive and year_id is not None and str(year_id).strip():
        return f"{key}::{str(year_id).strip()}"
    return key


def run_product_team_specialist(
    state: MyceliumGraphState | dict[str, Any],
    *,
    agent: SpecialistAgent,
    category: str,
    compute_attr: Callable[..., tuple[str | None, str, dict[str, str]]],
    scope_sensitive_fields: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Evaluate one team-scoped product attribute via ``compute_attr``."""
    current = coerce_state(state)
    ctx = current.context if isinstance(current.context, dict) else {}
    entity_id = resolve_entity_id(current)
    owned = resolve_owned_fields(current, category)
    thread_id, trace_id = current.invocation_thread_id, current.invocation_trace_id
    id_kwargs = {"thread_id": thread_id, "trace_id": trace_id}
    clf_kwargs = (
        {"classifications": current.classifications}
        if current.classifications
        else {}
    )
    identity_records = identity_from_context(ctx, entity_id)

    if not entity_id:
        resp = response_not_found(
            current.query,
            specialist=agent.agent_name,
            **id_kwargs,
            **clf_kwargs,
        )
        return {
            "response": resp,
            "route": None,
            "audit_log": [f"{agent.agent_name}: no id in state."],
            "specialist_contrib": {
                "id": None,
                "fields": owned,
                "values": {},
                "status": "not_found",
            },
            "matched_records": current.matched_records or [],
            "classifications": current.classifications or [],
        }

    paths = NetworkPaths.from_root(resolve_network_root())
    warehouse = default_warehouse_path(paths)
    team_id = entity_source_key(entity_id, LAHMAN_TEAM_ID, record_type="team")
    year_id = query_year_id(current)
    sources = load_pack_dataset_source(paths) or []
    now = now_iso()

    data = agent.storage.load()
    record = data.get("records", {}).get(entity_id, {})
    if not isinstance(record, dict):
        record = {}

    values: dict[str, Any] = {}
    na_attrs: list[str] = []
    found_attrs: list[str] = []
    sensitive = scope_sensitive_fields or frozenset()

    for field in owned:
        key = field.strip().lower()
        storage_key = _scoped_storage_key(
            key,
            year_id,
            scope_sensitive=key in sensitive,
        )
        entry = record.get(storage_key)
        if field_has_value(entry):
            values[key] = field_display_value(entry)
            found_attrs.append(key)
            continue
        if field_is_na(entry):
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        if not team_id:
            agent.write_na_field(entity_id, storage_key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        try:
            formatted, inline, parameters = compute_attr(
                key,
                team_id=team_id,
                warehouse=warehouse,
                year_id=year_id,
                paths=paths,
            )
        except FileNotFoundError:
            agent.write_na_field(entity_id, storage_key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        if formatted is None:
            agent.write_na_field(entity_id, storage_key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        written = agent.write_computed_field(
            entity_id,
            storage_key,
            value=formatted,
            sources=sources,
            computation={"language": "python", "inline": inline},
            parameters=parameters,
            at=now,
        )
        values[key] = written
        found_attrs.append(key)

    overall = overall_field_status(
        found_attrs=found_attrs,
        na_attrs=na_attrs,
        pending=[],
    )
    contrib = {
        "id": entity_id,
        "category": category,
        "fields": owned,
        "values": values,
        "status": overall,
        "researched_fields": [],
    }

    if overall == "found":
        resp = response_found(
            current.query,
            base_records=identity_records or None,
            specialist=agent.agent_name,
            **id_kwargs,
            **clf_kwargs,
        )
    else:
        resp = response_non_core(
            current.query,
            base_records=identity_records or None,
            attributes=owned,
            specialist=agent.agent_name,
            **id_kwargs,
            **clf_kwargs,
        )

    return {
        "response": resp,
        "route": None,
        "audit_log": [
            f"{agent.agent_name}: {overall} for id={entity_id!r} (category={category}).",
        ],
        "specialist_contrib": contrib,
        "matched_records": current.matched_records or [],
        "classifications": current.classifications or [],
        "context": ctx,
        "current_id": entity_id,
        "target_fields": owned,
    }


def team_roster_names(
    team_id: str,
    warehouse: Any,
    *,
    year_id: str | None,
) -> list[str]:
    if year_id is None or not str(year_id).strip():
        return []
    rows = query_warehouse(
        warehouse,
        '''
        SELECT DISTINCT TRIM(p."nameFirst") || ' ' || TRIM(p."nameLast") AS display_name
        FROM "Appearances" a
        JOIN "People" p ON p."playerID" = a."playerID"
        WHERE a."teamID" = ? AND a."yearID" = ?
          AND TRIM(COALESCE(p."nameFirst", "")) != ""
          AND TRIM(COALESCE(p."nameLast", "")) != ""
        ORDER BY display_name
        ''',
        (team_id, str(year_id).strip()),
    )
    return [str(row[0]).strip() for row in rows if row and row[0]]


def franchise_team_labels(team_id: str, warehouse: Any) -> tuple[list[str], str | None]:
    rows = query_warehouse(
        warehouse,
        'SELECT TRIM("franchID") FROM "Teams" WHERE "teamID" = ? LIMIT 1',
        (team_id,),
    )
    if not rows or not rows[0][0]:
        return [], None
    franch_id = str(rows[0][0]).strip()
    label_rows = query_warehouse(
        warehouse,
        'SELECT DISTINCT TRIM("name") FROM "Teams" WHERE "franchID" = ? ORDER BY "name"',
        (franch_id,),
    )
    labels = [str(row[0]).strip() for row in label_rows if row and row[0]]
    return labels, franch_id


def json_string_list(values: list[str]) -> str:
    return json.dumps(values, separators=(",", ":"))

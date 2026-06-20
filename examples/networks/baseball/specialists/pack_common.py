"""Shared graph helpers for baseball pack specialists."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

_bootstrap_path = Path(__file__).resolve().parent / "pack_bootstrap.py"
_bootstrap_spec = importlib.util.spec_from_file_location(
    "_baseball_pack_bootstrap",
    _bootstrap_path,
)
if _bootstrap_spec is None or _bootstrap_spec.loader is None:
    raise ImportError(f"Cannot load pack_bootstrap from {_bootstrap_path}")
_bootstrap_mod = importlib.util.module_from_spec(_bootstrap_spec)
_bootstrap_spec.loader.exec_module(_bootstrap_mod)
_bootstrap_mod.bootstrap(__file__)
from typing import Any, Callable

from agents.registry_bridge import entity_source_key
from agents.responses import response_found, response_non_core, response_not_found
from agents.specialists.agent import SpecialistAgent
from agents.specialists.fields import field_display_value, field_has_value, field_is_na
from models.state import MyceliumGraphState, graph_requested_attributes
from network.dataset_source import load_pack_dataset_source
from network.paths import NetworkPaths, resolve_network_root

from specialist_loader import load_warehouse_resolve

LAHMAN_PLAYER_ID = "lahman.playerID"
LAHMAN_TEAM_ID = "lahman.teamID"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def coerce_state(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def resolve_entity_id(state: MyceliumGraphState) -> str | None:
    if state.current_id:
        return state.current_id
    ctx = state.context if isinstance(state.context, dict) else {}
    entity_id = ctx.get("entity_id")
    if entity_id:
        return str(entity_id)
    if state.matched_records and len(state.matched_records) == 1:
        return state.matched_records[0].get("id")
    return None


def resolve_owned_fields(state: MyceliumGraphState, category: str) -> list[str]:
    if state.target_fields:
        return list(state.target_fields)
    owned: list[str] = []
    for cl in state.classifications or []:
        if cl.get("category") == category and cl.get("attribute"):
            owned.append(cl["attribute"])
    if owned:
        return owned
    return [
        attr.strip().lower()
        for attr in graph_requested_attributes(state)
        if attr.strip()
    ]


def identity_from_context(
    ctx: dict[str, Any],
    entity_id: str | None,
) -> list[dict[str, Any]]:
    bind = ctx.get("bind")
    if entity_id and isinstance(bind, dict):
        bind_values = {
            str(key): str(value)
            for key, value in bind.items()
            if value is not None and str(value).strip()
        }
        return [{"id": entity_id, "bind_values": bind_values}]
    return []


def overall_field_status(
    *,
    found_attrs: list[str],
    na_attrs: list[str],
    pending: list[str],
) -> str:
    if pending:
        return "pending"
    if found_attrs and not na_attrs:
        return "found"
    if na_attrs and not found_attrs:
        return "na"
    if na_attrs:
        return "mixed"
    return "pending"


def query_year_id(state: MyceliumGraphState) -> str | None:
    """Return yearID from step-1 query scope or step-2 delivery-bound scope."""
    raw_scope: dict[str, Any]
    if state.delivery_scope_query_scope:
        raw_scope = state.delivery_scope_query_scope
    else:
        raw_scope = state.query.scope or {}
    raw = raw_scope.get("yearID")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def evaluate_player_warehouse_fields(
    agent: SpecialistAgent,
    entity_id: str,
    owned: list[str],
    *,
    paths: NetworkPaths,
    domain: str,
    year_id: str | None = None,
    on_miss: Callable[[str], bool] | None = None,
    on_miss_resolve: Callable[..., Any] | None = None,
) -> tuple[dict[str, Any], str, list[str]]:
    """Resolve manifest aliases for a player-scoped warehouse domain."""
    wr = load_warehouse_resolve()
    data = agent.storage.load()
    record = data.get("records", {}).get(entity_id, {})
    if not isinstance(record, dict):
        record = {}

    sources = load_pack_dataset_source(paths) or []
    warehouse = wr.default_warehouse_path(paths)
    manifest = wr.load_manifest(paths)
    player_id = entity_source_key(entity_id, LAHMAN_PLAYER_ID)
    now = now_iso()
    values: dict[str, Any] = {}
    pending: list[str] = []
    na_attrs: list[str] = []
    found_attrs: list[str] = []
    audit: list[str] = []

    for field in owned:
        key = field.strip().lower()
        entry = record.get(key)
        if field_has_value(entry):
            values[key] = field_display_value(entry)
            found_attrs.append(key)
            continue
        if field_is_na(entry):
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        if not player_id or manifest is None:
            agent.write_na_field(entity_id, key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        try:
            resolved = wr.resolve_domain_attribute(
                key,
                domain=domain,
                manifest=manifest,
                player_id=player_id,
                warehouse=warehouse,
                year_id=year_id,
            )
        except FileNotFoundError:
            agent.write_na_field(entity_id, key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        if resolved is None and on_miss is not None and on_miss_resolve is not None:
            if on_miss(key):
                extra_values, extra_found, extra_na, extra_audit = on_miss_resolve(
                    agent,
                    entity_id,
                    key,
                    record=record,
                    player_id=player_id,
                    warehouse=warehouse,
                    manifest=manifest,
                    paths=paths,
                    sources=sources,
                    now=now,
                )
                values.update(extra_values)
                found_attrs.extend(extra_found)
                na_attrs.extend(extra_na)
                audit.extend(extra_audit)
                continue

        if resolved is None:
            agent.write_na_field(entity_id, key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        written = agent.write_computed_field(
            entity_id,
            key,
            value=resolved.value,
            sources=sources,
            computation={"language": "python", "inline": resolved.computation_inline},
            parameters=wr.provenance_parameters(
                player_id=player_id,
                paths=paths,
                warehouse=warehouse,
                attribute=resolved.attribute,
                column=resolved.column,
                year_id=year_id,
            ),
            at=now,
        )
        values[key] = written
        found_attrs.append(key)

    overall = overall_field_status(
        found_attrs=found_attrs,
        na_attrs=na_attrs,
        pending=pending,
    )
    return values, overall, audit


def evaluate_team_warehouse_fields(
    agent: SpecialistAgent,
    entity_id: str,
    owned: list[str],
    *,
    paths: NetworkPaths,
    domain: str,
    year_id: str | None = None,
) -> tuple[dict[str, Any], str]:
    wr = load_warehouse_resolve()
    data = agent.storage.load()
    record = data.get("records", {}).get(entity_id, {})
    if not isinstance(record, dict):
        record = {}

    sources = load_pack_dataset_source(paths) or []
    warehouse = wr.default_warehouse_path(paths)
    manifest = wr.load_manifest(paths)
    team_id = entity_source_key(entity_id, LAHMAN_TEAM_ID, record_type="team")
    now = now_iso()
    values: dict[str, Any] = {}
    pending: list[str] = []
    na_attrs: list[str] = []
    found_attrs: list[str] = []

    for field in owned:
        key = field.strip().lower()
        entry = record.get(key)
        if field_has_value(entry):
            values[key] = field_display_value(entry)
            found_attrs.append(key)
            continue
        if field_is_na(entry):
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        if not team_id or manifest is None:
            agent.write_na_field(entity_id, key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        try:
            resolved = wr.resolve_team_domain_attribute(
                key,
                domain=domain,
                manifest=manifest,
                team_id=team_id,
                warehouse=warehouse,
                year_id=year_id,
            )
        except FileNotFoundError:
            agent.write_na_field(entity_id, key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        if resolved is None:
            agent.write_na_field(entity_id, key, at=now)
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        written = agent.write_computed_field(
            entity_id,
            key,
            value=resolved.value,
            sources=sources,
            computation={"language": "python", "inline": resolved.computation_inline},
            parameters=wr.team_provenance_parameters(
                team_id=team_id,
                paths=paths,
                warehouse=warehouse,
                attribute=resolved.attribute,
                column=resolved.column,
                year_id=year_id,
            ),
            at=now,
        )
        values[key] = written
        found_attrs.append(key)

    overall = overall_field_status(
        found_attrs=found_attrs,
        na_attrs=na_attrs,
        pending=pending,
    )
    return values, overall


def run_warehouse_player_graph(
    state: MyceliumGraphState | dict[str, Any],
    *,
    agent: SpecialistAgent,
    category: str,
    domain: str,
    on_miss: Callable[[str], bool] | None = None,
    on_miss_resolve: Callable[..., Any] | None = None,
) -> dict[str, Any]:
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
    year_id = query_year_id(current)
    values, overall_status, derive_audit = evaluate_player_warehouse_fields(
        agent,
        entity_id,
        owned,
        paths=paths,
        domain=domain,
        year_id=year_id,
        on_miss=on_miss,
        on_miss_resolve=on_miss_resolve,
    )
    contrib = {
        "id": entity_id,
        "category": category,
        "fields": owned,
        "values": values,
        "status": overall_status,
        "researched_fields": [],
    }

    if overall_status == "found":
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
            f"{agent.agent_name}: {overall_status} for id={entity_id!r} "
            f"(category={category}).",
            *derive_audit,
        ],
        "specialist_contrib": contrib,
        "matched_records": current.matched_records or [],
        "classifications": current.classifications or [],
        "context": ctx,
        "current_id": entity_id,
        "target_fields": owned,
    }


def run_warehouse_team_graph(
    state: MyceliumGraphState | dict[str, Any],
    *,
    agent: SpecialistAgent,
    category: str,
    domain: str,
) -> dict[str, Any]:
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
    year_id = query_year_id(current)
    values, overall_status = evaluate_team_warehouse_fields(
        agent,
        entity_id,
        owned,
        paths=paths,
        domain=domain,
        year_id=year_id,
    )
    contrib = {
        "id": entity_id,
        "category": category,
        "fields": owned,
        "values": values,
        "status": overall_status,
        "researched_fields": [],
    }

    if overall_status == "found":
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
            f"{agent.agent_name}: {overall_status} for id={entity_id!r} "
            f"(category={category}).",
        ],
        "specialist_contrib": contrib,
        "matched_records": current.matched_records or [],
        "classifications": current.classifications or [],
        "context": ctx,
        "current_id": entity_id,
        "target_fields": owned,
    }
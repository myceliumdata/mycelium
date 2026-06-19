"""batting_specialist — warehouse-backed career batting stats (baseball pack)."""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.registry_bridge import entity_source_key
from agents.responses import response_found, response_non_core, response_not_found
from agents.specialists.agent import SpecialistAgent
from agents.specialists.fields import (
    field_display_value,
    field_has_value,
    field_is_na,
)
from models.state import MyceliumGraphState, graph_requested_attributes
from network.dataset_source import load_pack_dataset_source
from network.paths import NetworkPaths, resolve_network_root
from network.warehouse import default_warehouse_path, query_warehouse

LAHMAN_PLAYER_ID = "lahman.playerID"


def career_hr(player_id: str, warehouse: Path) -> int:
    rows = query_warehouse(
        warehouse,
        'SELECT COALESCE(SUM(CAST("HR" AS INTEGER)), 0) FROM "Batting" WHERE "playerID" = ?',
        (player_id,),
    )
    return int(rows[0][0]) if rows else 0


CAREER_HR_COMPUTATION_INLINE = inspect.getsource(career_hr)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _resolve_id(state: MyceliumGraphState) -> str | None:
    if state.current_id:
        return state.current_id
    ctx = state.context if isinstance(state.context, dict) else {}
    entity_id = ctx.get("entity_id")
    if entity_id:
        return str(entity_id)
    if state.matched_records and len(state.matched_records) == 1:
        return state.matched_records[0].get("id")
    return None


def _resolve_owned_fields(state: MyceliumGraphState) -> list[str]:
    if state.target_fields:
        return list(state.target_fields)
    owned: list[str] = []
    for cl in state.classifications or []:
        if cl.get("category") == "batting" and cl.get("attribute"):
            owned.append(cl["attribute"])
    if owned:
        return owned
    return [
        attr.strip().lower()
        for attr in graph_requested_attributes(state)
        if attr.strip()
    ]


def _identity_from_context(ctx: dict[str, Any], entity_id: str | None) -> list[dict[str, Any]]:
    bind = ctx.get("bind")
    if entity_id and isinstance(bind, dict):
        bind_values = {
            str(key): str(value)
            for key, value in bind.items()
            if value is not None and str(value).strip()
        }
        return [{"id": entity_id, "bind_values": bind_values}]
    return []


def _overall_field_status(
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


def _evaluate_batting_fields(
    agent: SpecialistAgent,
    entity_id: str,
    owned: list[str],
    *,
    paths: NetworkPaths,
) -> tuple[dict[str, Any], str]:
    data = agent.storage.load()
    record = data.get("records", {}).get(entity_id, {})
    if not isinstance(record, dict):
        record = {}

    sources = load_pack_dataset_source(paths) or []
    warehouse = default_warehouse_path(paths)
    player_id = entity_source_key(entity_id, LAHMAN_PLAYER_ID)
    now = _now_iso()
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

        if key == "career_hr":
            if not player_id:
                agent.write_na_field(entity_id, key, at=now)
                values[key] = "N/A"
                na_attrs.append(key)
                continue
            try:
                total = career_hr(player_id, warehouse)
            except FileNotFoundError:
                agent.write_na_field(entity_id, key, at=now)
                values[key] = "N/A"
                na_attrs.append(key)
                continue
            written = agent.write_computed_field(
                entity_id,
                key,
                value=str(total),
                sources=sources,
                computation={"language": "python", "inline": CAREER_HR_COMPUTATION_INLINE},
                parameters={LAHMAN_PLAYER_ID: player_id},
                at=now,
            )
            values[key] = written
            found_attrs.append(key)
            continue

        agent.write_na_field(entity_id, key, at=now)
        values[key] = "N/A"
        na_attrs.append(key)

    overall = _overall_field_status(
        found_attrs=found_attrs,
        na_attrs=na_attrs,
        pending=pending,
    )
    return values, overall


def _run_batting_specialist_graph(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    current = _coerce(state)
    ctx = current.context if isinstance(current.context, dict) else {}
    pid = _resolve_id(current)
    owned = _resolve_owned_fields(current)
    thread_id, trace_id = current.invocation_thread_id, current.invocation_trace_id
    id_kwargs = {"thread_id": thread_id, "trace_id": trace_id}
    clf_kwargs = (
        {"classifications": current.classifications}
        if current.classifications
        else {}
    )
    identity_records = _identity_from_context(ctx, pid)

    if not pid:
        resp = response_not_found(current.query, specialist="batting_specialist", **id_kwargs, **clf_kwargs)
        return {
            "response": resp,
            "route": None,
            "audit_log": ["batting_specialist: no id in state."],
            "specialist_contrib": {"id": None, "fields": owned, "values": {}, "status": "not_found"},
            "matched_records": current.matched_records or [],
            "classifications": current.classifications or [],
        }

    paths = NetworkPaths.from_root(resolve_network_root())
    values, overall_status = _evaluate_batting_fields(AGENT, pid, owned, paths=paths)
    contrib = {
        "id": pid,
        "category": "batting",
        "fields": owned,
        "values": values,
        "status": overall_status,
        "researched_fields": [],
    }

    if overall_status == "found":
        resp = response_found(
            current.query,
            base_records=identity_records or None,
            specialist="batting_specialist",
            **id_kwargs,
            **clf_kwargs,
        )
    else:
        resp = response_non_core(
            current.query,
            base_records=identity_records or None,
            attributes=owned,
            specialist="batting_specialist",
            **id_kwargs,
            **clf_kwargs,
        )

    return {
        "response": resp,
        "route": None,
        "audit_log": [
            f"batting_specialist: {overall_status} for id={pid!r} (category=batting).",
        ],
        "specialist_contrib": contrib,
        "matched_records": current.matched_records or [],
        "classifications": current.classifications or [],
        "context": ctx,
        "current_id": pid,
        "target_fields": owned,
    }


class BattingSpecialist(SpecialistAgent):
    category = "batting"
    agent_name = "batting_specialist"

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        return _run_batting_specialist_graph(state)


AGENT = BattingSpecialist()


def batting_specialist(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return AGENT.run(state)

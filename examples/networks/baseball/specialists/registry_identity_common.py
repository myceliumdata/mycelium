"""Shared registry bind-field reads for player/team identity specialists."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

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

from agents.entity_registry import get_entity_registry
from agents.responses import response_found, response_non_core, response_not_found
from agents.specialists.agent import SpecialistAgent
from agents.specialists.fields import (
    append_version,
    current_value,
    current_version,
    field_display_value,
    field_has_value,
    field_is_na,
)
from models.state import MyceliumGraphState
from network.mvr import load_mvr

from pack_common import (
    coerce_state,
    identity_from_context,
    now_iso,
    overall_field_status,
    resolve_entity_id,
    resolve_owned_fields,
)


def _version_actor_kind(entry: Any) -> str | None:
    version = current_version(entry)
    if not isinstance(version, dict):
        return None
    actor = version.get("actor")
    if not isinstance(actor, dict):
        return None
    kind = actor.get("kind")
    return str(kind) if isinstance(kind, str) else None


def _bind_values_for_fields(
    entity_id: str,
    fields: list[str],
    ctx: dict[str, Any],
    *,
    record_type: str,
) -> dict[str, str]:
    keys = [field.strip().lower() for field in fields if field.strip()]
    out: dict[str, str] = {}
    bind = ctx.get("bind")
    if isinstance(bind, dict):
        for key in keys:
            raw = bind.get(key)
            if raw is not None and str(raw).strip():
                out[key] = str(raw).strip()
    missing = [key for key in keys if key not in out]
    if missing:
        entity = get_entity_registry(record_type=record_type).lookup_by_id(entity_id)
        if entity is not None:
            for key in missing:
                value = entity.bind_value(key)
                if value is not None:
                    out[key] = value
    allowed = frozenset(load_mvr(record_type=record_type).bind_fields)
    return {key: value for key, value in out.items() if key in allowed}


def _write_registry_version(
    agent: SpecialistAgent,
    entity_id: str,
    key: str,
    value: str,
    *,
    at: str,
) -> str:
    data = agent.storage.load()
    records = data.setdefault("records", {})
    record = records.setdefault(entity_id, {})
    version_body: dict[str, Any] = {
        "at": at,
        "status": "found",
        "value": value.strip(),
        "actor": {
            "kind": "registry",
            "category": agent.category,
            "specialist": agent.agent_name,
        },
    }
    record[key] = append_version(record.get(key), version_body)
    agent.storage.save(data)
    return current_value(record[key]) or value.strip()


def _evaluate_registry_identity_fields(
    agent: SpecialistAgent,
    entity_id: str,
    owned: list[str],
    *,
    ctx: dict[str, Any],
    record_type: str,
) -> tuple[dict[str, Any], str]:
    data = agent.storage.load()
    record = data.get("records", {}).get(entity_id, {})
    if not isinstance(record, dict):
        record = {}

    bind_values = _bind_values_for_fields(
        entity_id,
        owned,
        ctx,
        record_type=record_type,
    )
    now = now_iso()
    values: dict[str, Any] = {}
    pending: list[str] = []
    na_attrs: list[str] = []
    found_attrs: list[str] = []

    for field in owned:
        key = field.strip().lower()
        entry = record.get(key)
        if field_has_value(entry):
            raw = bind_values.get(key)
            if raw is not None and _version_actor_kind(entry) == "research":
                values[key] = _write_registry_version(
                    agent,
                    entity_id,
                    key,
                    raw,
                    at=now,
                )
                found_attrs.append(key)
                continue
            values[key] = field_display_value(entry)
            found_attrs.append(key)
            continue
        if field_is_na(entry):
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        raw = bind_values.get(key)
        if raw is None:
            agent.write_na_field(entity_id, key, at=now, actor_kind="registry")
            values[key] = "N/A"
            na_attrs.append(key)
            continue

        written = agent.write_fields(
            entity_id,
            {key: raw},
            actor_kind="registry",
            at=now,
        )
        values[key] = written.get(key, raw)
        found_attrs.append(key)

    overall = overall_field_status(
        found_attrs=found_attrs,
        na_attrs=na_attrs,
        pending=pending,
    )
    return values, overall


def run_registry_identity_graph(
    state: MyceliumGraphState | dict[str, Any],
    *,
    agent: SpecialistAgent,
    category: str,
    record_type: str,
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

    values, overall_status = _evaluate_registry_identity_fields(
        agent,
        entity_id,
        owned,
        ctx=ctx,
        record_type=record_type,
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
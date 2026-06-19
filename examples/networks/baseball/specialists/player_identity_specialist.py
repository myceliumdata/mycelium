"""player_identity_specialist — registry bind fields for player MVR (baseball pack)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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
from models.state import MyceliumGraphState, graph_requested_attributes
from network.mvr import load_mvr


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
        if cl.get("category") == "player_identity" and cl.get("attribute"):
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


def _bind_values_for_fields(
    entity_id: str,
    fields: list[str],
    ctx: dict[str, Any],
) -> dict[str, str]:
    """Read MVR bind values from graph context or entity registry."""
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
        entity = get_entity_registry(record_type="player").lookup_by_id(entity_id)
        if entity is not None:
            for key in missing:
                value = entity.bind_value(key)
                if value is not None:
                    out[key] = value
    allowed = frozenset(load_mvr(record_type="player").bind_fields)
    return {key: value for key, value in out.items() if key in allowed}


def _version_actor_kind(entry: Any) -> str | None:
    version = current_version(entry)
    if not isinstance(version, dict):
        return None
    actor = version.get("actor")
    if not isinstance(actor, dict):
        return None
    kind = actor.get("kind")
    return str(kind) if isinstance(kind, str) else None


def _write_registry_version(
    agent: SpecialistAgent,
    entity_id: str,
    key: str,
    value: str,
    *,
    at: str,
) -> str:
    """Append a registry-sourced version (used when replacing research contamination)."""
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


def _evaluate_player_identity_fields(
    agent: SpecialistAgent,
    entity_id: str,
    owned: list[str],
    *,
    ctx: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    data = agent.storage.load()
    record = data.get("records", {}).get(entity_id, {})
    if not isinstance(record, dict):
        record = {}

    bind_values = _bind_values_for_fields(entity_id, owned, ctx)
    now = _now_iso()
    values: dict[str, Any] = {}
    pending: list[str] = []
    na_attrs: list[str] = []
    found_attrs: list[str] = []

    for field in owned:
        key = field.strip().lower()
        entry = record.get(key)
        if field_has_value(entry):
            raw = bind_values.get(key)
            cached = field_display_value(entry)
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
            values[key] = cached
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

    overall = _overall_field_status(
        found_attrs=found_attrs,
        na_attrs=na_attrs,
        pending=pending,
    )
    return values, overall


def _run_player_identity_specialist_graph(
    state: MyceliumGraphState | dict[str, Any],
) -> dict[str, Any]:
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
        resp = response_not_found(
            current.query,
            specialist="player_identity_specialist",
            **id_kwargs,
            **clf_kwargs,
        )
        return {
            "response": resp,
            "route": None,
            "audit_log": ["player_identity_specialist: no id in state."],
            "specialist_contrib": {
                "id": None,
                "fields": owned,
                "values": {},
                "status": "not_found",
            },
            "matched_records": current.matched_records or [],
            "classifications": current.classifications or [],
        }

    values, overall_status = _evaluate_player_identity_fields(
        AGENT,
        pid,
        owned,
        ctx=ctx,
    )
    contrib = {
        "id": pid,
        "category": "player_identity",
        "fields": owned,
        "values": values,
        "status": overall_status,
        "researched_fields": [],
    }

    if overall_status == "found":
        resp = response_found(
            current.query,
            base_records=identity_records or None,
            specialist="player_identity_specialist",
            **id_kwargs,
            **clf_kwargs,
        )
    else:
        resp = response_non_core(
            current.query,
            base_records=identity_records or None,
            attributes=owned,
            specialist="player_identity_specialist",
            **id_kwargs,
            **clf_kwargs,
        )

    return {
        "response": resp,
        "route": None,
        "audit_log": [
            f"player_identity_specialist: {overall_status} for id={pid!r} "
            "(category=player_identity).",
        ],
        "specialist_contrib": contrib,
        "matched_records": current.matched_records or [],
        "classifications": current.classifications or [],
        "context": ctx,
        "current_id": pid,
        "target_fields": owned,
    }


class PlayerIdentitySpecialist(SpecialistAgent):
    category = "player_identity"
    agent_name = "player_identity_specialist"

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        return _run_player_identity_specialist_graph(state)


AGENT = PlayerIdentitySpecialist()


def player_identity_specialist(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return AGENT.run(state)

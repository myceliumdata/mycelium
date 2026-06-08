"""Graph nodes: build context, invoke specialists, assemble QueryResponse."""

from __future__ import annotations

from typing import Any

from agents.context import get_context_builder
from agents.registry import get_agent_registry
from agents.responses import (
    merge_requested_record,
    response_assembled,
    response_found,
    response_not_found,
)
from agents.supervisor import _identity_records_from_seed, _target_fields_for_agent
from models.state import MyceliumGraphState, normalized_requested_attributes


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _meta(state: MyceliumGraphState) -> dict[str, Any]:
    ctx = state.context if isinstance(state.context, dict) else {}
    meta = ctx.get("_meta")
    return meta if isinstance(meta, dict) else {}


def build_context_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Pull seed + all specialist storage for matched id(s) into state.context."""
    current = _coerce(state)
    meta = _meta(current)
    ids = list(meta.get("ids") or [])
    if current.current_id and current.current_id not in ids:
        ids.append(current.current_id)

    builder = get_context_builder()
    full_ctx = builder.build_full_context(
        ids,
        seed_records=current.matched_records or None,
    )
    meta = dict(meta)
    meta.setdefault("specialists_to_invoke", [])
    meta.setdefault("contributions", [])

    merged: dict[str, Any] = {
        "seed": full_ctx.get("seed"),
        "specialists": full_ctx.get("specialists", {}),
        "_meta": meta,
    }
    n_cats = len(merged.get("specialists") or {})
    logs = [
        f"build_context: built context from {n_cats} specialist store(s) "
        f"for {len(ids)} id(s).",
    ]
    return {"context": merged, "audit_log": logs}


def invoke_specialists_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Sequentially invoke each required specialist with full context + owned fields."""
    current = _coerce(state)
    meta = _meta(current)
    to_invoke: list[str] = list(meta.get("specialists_to_invoke") or [])
    contributions: list[dict[str, Any]] = list(meta.get("contributions") or [])
    logs: list[str] = []
    registry = get_agent_registry()

    for agent_name in to_invoke:
        fn = registry.get_agent_fn(agent_name)
        if fn is None:
            logs.append(f"invoke_specialists: skip {agent_name} (not registered).")
            continue
        target_fields = _target_fields_for_agent(
            agent_name,
            current.classifications or [],
        )
        enriched = current.model_copy(
            update={
                "context": current.context,
                "current_id": current.current_id,
                "target_fields": target_fields,
                "route": agent_name,
            },
        )
        result = fn(enriched)
        contributions.append(
            {
                "agent": agent_name,
                "target_fields": target_fields,
                "specialist_contrib": result.get("specialist_contrib"),
                "response": result.get("response"),
            },
        )
        logs.append(
            f"invoke_specialists: invoked {agent_name} with context "
            f"({len(target_fields)} owned field(s)).",
        )
        if result.get("audit_log"):
            logs.extend(result["audit_log"])

    meta = dict(meta)
    meta["contributions"] = contributions
    ctx = dict(current.context) if isinstance(current.context, dict) else {}
    ctx["_meta"] = meta
    return {"context": ctx, "audit_log": logs, "route": None}


def assemble_response_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Produce final QueryResponse from seed matches and specialist contributions."""
    current = _coerce(state)
    query = current.query
    thread_id = current.invocation_thread_id
    trace_id = current.invocation_trace_id
    id_kwargs = {"thread_id": thread_id, "trace_id": trace_id}
    clf_kwargs = (
        {"classifications": current.classifications}
        if current.classifications
        else {}
    )
    meta = _meta(current)
    contributions = meta.get("contributions") or []
    matched = current.matched_records or []

    if not matched:
        return {
            "response": response_not_found(query, **id_kwargs, **clf_kwargs),
            "audit_log": ["assemble_response: no seed match."],
        }

    requested = normalized_requested_attributes(query.requested_attributes)

    if not requested:
        identity_records = _identity_records_from_seed(matched)
        return {
            "response": response_found(
                query,
                base_records=identity_records,
                **id_kwargs,
                **clf_kwargs,
            ),
            "audit_log": ["assemble_response: seed identity response."],
        }

    merged_records: list[dict[str, Any]] = []
    for seed_rec in matched:
        merged, _provisional, _unavailable = merge_requested_record(
            seed_rec,
            contributions,
            requested,
        )
        merged_records.append(merged)

    debug_extra: dict[str, Any] = {
        "context_specialist_categories": list(
            (current.context or {}).get("specialists", {}).keys(),
        ),
        "contributions": len(contributions),
    }
    if current.classifications:
        debug_extra["classifications"] = current.classifications

    resp = response_assembled(
        query,
        merged_records=merged_records,
        classifications=current.classifications or [],
        contributions=contributions,
        audit_log=current.audit_log,
        debug_extra=debug_extra,
        **id_kwargs,
    )
    if contributions:
        audit = "assemble_response: merged specialist contributions."
    else:
        audit = "assemble_response: requested attrs, no contributions."

    return {"response": resp, "audit_log": [audit]}


# Legacy name used by older graph wiring (replaced by invoke_specialists_node).
def specialist_dispatcher(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return invoke_specialists_node(state)
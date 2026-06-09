"""Graph nodes: build context, invoke specialists, assemble QueryResponse."""

from __future__ import annotations

from typing import Any

from agents.context import get_context_builder
from agents.entity_registry import get_entity_registry, registry_entity_to_match
from agents.entity_resolution import is_provisional_registry_match
from agents.entity_validation import (
    run_mvr_validation,
    validation_all_passed,
    validation_failure_summary,
)
from agents.registry import get_agent_registry
from agents.research_gate import is_research_gated, research_gate_allows
from agents.responses import (
    merge_requested_record,
    response_assembled,
    response_entity_bound_provisional,
    response_entity_under_specified,
    response_entity_unknown,
    response_entity_unresolved,
    response_entity_validated,
    response_found,
    response_not_found,
    response_research_gated,
    response_validation_failed,
)
from agents.supervisor import (
    _collect_specialists_to_invoke,
    _identity_records_from_seed,
    _target_fields_for_agent,
)
from models.state import MyceliumGraphState, normalized_requested_attributes


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _meta(state: MyceliumGraphState) -> dict[str, Any]:
    ctx = state.context if isinstance(state.context, dict) else {}
    meta = ctx.get("_meta")
    return meta if isinstance(meta, dict) else {}


def validate_entity_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Run MVR validation on provisional registry entities; promote when all pass."""
    current = _coerce(state)
    matched = current.matched_records or []
    if len(matched) != 1 or not is_provisional_registry_match(matched[0]):
        return {
            "validation_passed": None,
            "validation_contributions": [],
            "audit_log": ["validate_entity: skip (not provisional registry)."],
        }

    entity_id = matched[0].get("id")
    if not entity_id:
        return {"audit_log": ["validate_entity: skip (no entity id)."]}

    registry = get_entity_registry()
    entity = registry.lookup_by_id(str(entity_id))
    if entity is None:
        return {"audit_log": ["validate_entity: skip (registry row missing)."]}

    contribs = run_mvr_validation(entity.name, entity.employer)
    logs = ["validate_entity: ran MVR validation on provisional registry entity."]
    for item in contribs:
        vc = item.get("validation_contrib") or {}
        logs.append(
            f"validate_entity: {item.get('agent')} "
            f"{vc.get('field')} -> {vc.get('status')}.",
        )

    if not validation_all_passed(contribs):
        summary = validation_failure_summary(contribs)
        return {
            "validation_passed": False,
            "validation_contributions": contribs,
            "audit_log": logs + [f"validate_entity: failed ({summary})."],
        }

    updated = registry.promote_validated(str(entity_id))
    updated_match = registry_entity_to_match(updated)
    ctx = dict(current.context) if isinstance(current.context, dict) else {}
    meta = dict(_meta(current))
    meta["ids"] = [updated.id]
    specialists_to_invoke: list[str] = []
    if (
        current.query.requested_attributes
        and current.classifications
        and research_gate_allows(current_id=updated.id, matched=[updated_match])
    ):
        audit: list[str] = []
        specialists_to_invoke = _collect_specialists_to_invoke(
            current.classifications,
            audit,
        )
        logs.extend(audit)
        if specialists_to_invoke:
            logs.append(
                "validate_entity: validation passed — scheduling attribute specialists.",
            )
    meta["specialists_to_invoke"] = specialists_to_invoke
    meta.setdefault("contributions", [])
    ctx.update(
        {
            "seed": updated_match,
            "specialists": ctx.get("specialists") or {},
            "_meta": meta,
        },
    )

    return {
        "matched_records": [updated_match],
        "current_id": updated.id,
        "validation_passed": True,
        "validation_contributions": contribs,
        "context": ctx,
        "audit_log": logs + ["validate_entity: promoted to validated."],
    }


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

    if current.entity_resolution_kind == "suggest" and current.entity_suggestions:
        return {
            "response": response_entity_unresolved(
                query,
                current.entity_suggestions,
                **id_kwargs,
            ),
            "audit_log": ["assemble_response: entity key unresolved (suggestions)."],
        }

    if current.entity_resolution_kind == "unknown":
        return {
            "response": response_entity_unknown(query, **id_kwargs),
            "audit_log": ["assemble_response: entity unknown (MVR required)."],
        }

    if current.entity_resolution_kind == "under_specified":
        return {
            "response": response_entity_under_specified(
                query,
                current.entity_required_fields,
                **id_kwargs,
            ),
            "audit_log": ["assemble_response: entity under-specified (partial binding)."],
        }

    if current.validation_passed is False and matched:
        summary = validation_failure_summary(current.validation_contributions)
        return {
            "response": response_validation_failed(
                query,
                matched[0],
                summary=summary,
                **id_kwargs,
            ),
            "audit_log": ["assemble_response: validation failed (stay provisional)."],
        }

    if (
        current.validation_passed is True
        and current.validation_contributions
        and matched
        and not normalized_requested_attributes(query.requested_attributes)
    ):
        return {
            "response": response_entity_validated(query, matched[0], **id_kwargs),
            "audit_log": ["assemble_response: entity validated."],
        }

    if is_research_gated(current):
        return {
            "response": response_research_gated(query, matched[0], **id_kwargs),
            "audit_log": ["assemble_response: research gate (provisional + attrs)."],
        }

    if (
        current.entity_resolution_kind == "bind_provisional"
        and matched
        and current.validation_passed is not True
    ):
        return {
            "response": response_entity_bound_provisional(
                query,
                matched[0],
                **id_kwargs,
            ),
            "audit_log": ["assemble_response: entity bound provisional."],
        }

    if not matched:
        return {
            "response": response_not_found(query, **id_kwargs, **clf_kwargs),
            "audit_log": ["assemble_response: no seed match."],
        }

    requested = normalized_requested_attributes(query.requested_attributes)

    if not requested:
        identity_records = _identity_records_from_seed(matched)
        message = None
        if current.duplicate_bind and len(matched) == 1:
            name = matched[0].get("name") or query.entity_key
            employer = matched[0].get("employer")
            employer_phrase = f" at {employer}" if employer else ""
            if matched[0].get("_validation_state") == "validated":
                message = f"Already bound record for {name}{employer_phrase}."
            else:
                message = (
                    f"Already bound provisional record for {name}{employer_phrase}."
                )
        return {
            "response": response_found(
                query,
                base_records=identity_records,
                message=message,
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

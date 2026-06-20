"""Graph nodes: build context, invoke specialists, assemble QueryResponse."""

from __future__ import annotations

from typing import Any

from agents.context import bind_from_record, get_context_builder, planner_context
from agents.entity_growth import apply_registry_research_attribution, parse_research_fields_updated
from agents.entity_registry import get_entity_registry, registry_entity_to_match
from agents.entity_resolution import is_provisional_registry_match
from agents.entity_validation import (
    run_mvr_validation,
    validation_all_passed,
    validation_failure_summary,
)
from agents.registry import get_agent_registry
from agents.research_gate import is_research_gated, research_gate_allows
from agents.metering_gate import write_entitlement_from_accepted_quote
from agents.responses import (
    _identity_message_label,
    _identity_records_from_match,
    merge_requested_record,
    response_assembled,
    response_found,
    response_lookup_incomplete,
    response_lookup_resolved,
    response_lookup_suggested,
    response_not_found,
    response_principal_required,
    response_payment_required,
    response_quote_required,
    response_research_gated,
    response_validation_failed,
)
from agents.target_deliver import (
    delivery_scope_has_attributes,
    hydrate_matches_for_deliver,
    load_delivery_scope,
)
from network.delivery_hints import delivery_not_found_message
from network.paths import resolve_network_root
from agents.target_metering import (
    delivery_payload_from_scope,
    run_target_metering_gate,
    step1_should_quote,
    step2_should_quote,
)
from agents.target_resolve import issue_target_delivery, resolve_target_step1
from agents.supervisor import (
    _collect_specialists_to_invoke,
    _target_fields_for_agent,
)
from models.state import (
    EntityQuery,
    MyceliumGraphState,
    QueryResponse,
    entity_query_is_delivery_step,
    graph_provenance_requested,
    graph_requested_attributes,
)
from network.delivery import DeliveryScope, get_delivery_store
from network.metering_policy import load_metering_policy
from network.mvr import default_record_type


def _state_with_resolve_record_type(
    current: MyceliumGraphState,
    record_type: str | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Attach resolved MVR record type to graph context for downstream registry access."""
    if not record_type:
        return result
    ctx = dict(current.context) if isinstance(current.context, dict) else {}
    meta_raw = ctx.get("_meta")
    meta = dict(meta_raw) if isinstance(meta_raw, dict) else {}
    meta["resolve_record_type"] = record_type
    ctx["_meta"] = meta
    result["context"] = ctx
    return result


def _target_metering_block_response(
    query: EntityQuery,
    scope: DeliveryScope,
    gate,
    *,
    total_matches: int | None,
    id_kwargs: dict[str, Any],
) -> dict[str, Any] | None:
    delivery = delivery_payload_from_scope(scope)
    if gate.kind == "principal_required":
        return {
            "response": response_principal_required(
                query,
                funding_model=gate.funding_model or "",
                **id_kwargs,
            ),
            "audit_log": ["target_resolve: principal_required."],
        }
    if gate.kind == "payment_required" and gate.quote:
        return {
            "response": response_payment_required(query, gate.quote, **id_kwargs),
            "audit_log": ["target_resolve: payment_required."],
        }
    if gate.kind == "quote_required" and gate.quote:
        return {
            "response": response_quote_required(
                query,
                gate.quote,
                total_matches=total_matches,
                delivery=delivery,
                **id_kwargs,
            ),
            "audit_log": ["target_resolve: quote_required."],
        }
    return None


def _target_metering_entitlement_state(gate) -> dict[str, Any]:
    if gate.kind != "accepted":
        return {}
    return {
        "metering_accepted_quote": gate.accepted_quote,
        "metering_write_entitlement": gate.write_entitlement,
    }


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _meta(state: MyceliumGraphState) -> dict[str, Any]:
    ctx = state.context if isinstance(state.context, dict) else {}
    meta = ctx.get("_meta")
    return meta if isinstance(meta, dict) else {}


def target_resolve_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Target protocol step-1 resolve or step-2 deliver (M4/M5)."""
    current = _coerce(state)
    query = current.query
    id_kwargs = {
        "thread_id": current.invocation_thread_id,
        "trace_id": current.invocation_trace_id,
    }

    if entity_query_is_delivery_step(query):
        delivery_id = (query.delivery_id or "").strip()
        loaded = load_delivery_scope(delivery_id)
        if loaded.kind == "not_found" or loaded.scope is None:
            return {
                "response": response_not_found(
                    query,
                    message=delivery_not_found_message(
                        delivery_id,
                        active_root=resolve_network_root(),
                    ),
                    **id_kwargs,
                ),
                "audit_log": ["target_resolve: deliver not_found (missing or expired scope)."],
            }

        try:
            scope, matched, resolution_kind = hydrate_matches_for_deliver(loaded)
        except ValueError:
            return {
                "response": response_not_found(
                    query,
                    message=delivery_not_found_message(
                        delivery_id,
                        active_root=resolve_network_root(),
                    ),
                    **id_kwargs,
                ),
                "audit_log": ["target_resolve: deliver not_found (scope hydration failed)."],
            }

        resolve_record_type = scope.record_type or default_record_type()
        policy = load_metering_policy()
        metering_state: dict[str, Any] = {}
        if step2_should_quote(policy):
            gate = run_target_metering_gate(
                query=query,
                scope=scope,
                quote_id=query.quote_id,
                principal=query.principal,
                require_quote=True,
            )
            match_count = len(scope.entity_ids) or (1 if scope.create_on_deliver else 0)
            blocked = _target_metering_block_response(
                query,
                scope,
                gate,
                total_matches=match_count,
                id_kwargs=id_kwargs,
            )
            if blocked is not None:
                return blocked
            metering_state = _target_metering_entitlement_state(gate)

        if delivery_scope_has_attributes(scope):
            result: dict[str, Any] = {
                **metering_state,
                "matched_records": matched,
                "entity_resolution_kind": resolution_kind,
                "delivery_scope_attrs": list(scope.requested_attributes),
                "delivery_scope_provenance": bool(scope.provenance),
                "delivery_scope_query_scope": dict(scope.query_scope or {}),
                "audit_log": [
                    f"target_resolve: deliver step-2 attrs="
                    f"{scope.requested_attributes!r} entity_count={len(matched)}.",
                ],
            }
            if len(matched) == 1:
                result["current_id"] = matched[0].get("id")
            return _state_with_resolve_record_type(current, resolve_record_type, result)

        if any(is_provisional_registry_match(rec) for rec in matched):
            result = {
                **metering_state,
                "matched_records": matched,
                "entity_resolution_kind": resolution_kind,
                "audit_log": [
                    "target_resolve: deliver step-2 identity "
                    f"entity_count={len(matched)} (validation pending).",
                ],
            }
            if len(matched) == 1:
                result["current_id"] = matched[0].get("id")
            return _state_with_resolve_record_type(current, resolve_record_type, result)

        identity_records = _identity_records_from_match(
            matched,
            record_type=resolve_record_type,
        )
        message = None
        if len(matched) == 1:
            message = (
                f"Found record for {_identity_message_label(matched[0], query=query)}."
            )
        else:
            message = f"Found {len(matched)} records for delivery."
        resp = response_found(
            query,
            base_records=identity_records,
            message=message,
            **id_kwargs,
        )
        return {
            "response": _attach_provenance(resp, current, matched),
            "audit_log": [
                f"target_resolve: deliver found entity_count={len(matched)}.",
            ],
        }

    resolved = resolve_target_step1(query)
    if resolved.kind == "not_found":
        if (query.id or "").strip():
            message = f"No record found for id {(query.id or '').strip()!r}."
        else:
            message = f"No records found for lookup {query.lookup!r}."
        return {
            "response": response_not_found(query, message=message, **id_kwargs),
            "audit_log": ["target_resolve: not_found (no delivery issued)."],
        }

    if resolved.kind == "lookup_incomplete":
        return {
            "response": response_lookup_incomplete(
                query,
                required_fields=list(resolved.required_fields),
                **id_kwargs,
            ),
            "audit_log": [
                "target_resolve: lookup_incomplete "
                f"required_fields={resolved.required_fields!r}.",
            ],
        }

    if resolved.kind == "lookup_suggested":
        return {
            "response": response_lookup_suggested(
                query,
                suggestions=list(resolved.suggestions),
                **id_kwargs,
            ),
            "audit_log": [
                f"target_resolve: lookup_suggested count={len(resolved.suggestions)}.",
            ],
        }

    if resolved.kind not in {"resolved", "create_pending"} or (
        resolved.kind == "resolved" and not resolved.entity_ids
    ):
        return {
            "response": response_not_found(query, message="Resolve failed.", **id_kwargs),
            "audit_log": ["target_resolve: not_found (unexpected resolve kind)."],
        }

    delivery = issue_target_delivery(
        query,
        resolved.entity_ids,
        create_on_deliver=resolved.create_on_deliver,
        record_type=resolved.record_type,
    )
    total = len(resolved.entity_ids)
    scope = get_delivery_store().get(delivery.delivery_id)
    if scope is None:
        return {
            "response": response_not_found(
                query,
                message="Delivery scope missing after issue.",
                **id_kwargs,
            ),
            "audit_log": ["target_resolve: not_found (delivery store miss)."],
        }

    policy = load_metering_policy()
    if step1_should_quote(scope, policy):
        gate = run_target_metering_gate(
            query=query,
            scope=scope,
            principal=query.principal,
            require_quote=True,
        )
        blocked = _target_metering_block_response(
            query,
            scope,
            gate,
            total_matches=total,
            id_kwargs=id_kwargs,
        )
        if blocked is not None:
            return blocked

    return {
        "response": response_lookup_resolved(
            query,
            total_matches=total,
            delivery=delivery,
            **id_kwargs,
        ),
        "audit_log": [
            f"target_resolve: lookup_resolved total_matches={total} "
            f"delivery_id={delivery.delivery_id!r}.",
        ],
    }


def validate_entity_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Run MVR validation on provisional registry entities; promote when all pass."""
    current = _coerce(state)
    matched = list(current.matched_records or [])
    if not matched:
        return {
            "validation_passed": None,
            "validation_contributions": [],
            "audit_log": ["validate_entity: skip (no matches)."],
        }

    registry = get_entity_registry(
        record_type=_meta(current).get("resolve_record_type") or default_record_type(),
    )
    updated_matches: list[dict[str, Any]] = []
    all_contribs: list[dict[str, Any]] = []
    logs: list[str] = []
    processed_provisional = False
    any_failed = False

    for rec in matched:
        if not is_provisional_registry_match(rec):
            updated_matches.append(rec)
            continue

        processed_provisional = True
        entity_id = rec.get("id")
        if not entity_id:
            updated_matches.append(rec)
            continue

        entity = registry.lookup_by_id(str(entity_id))
        if entity is None:
            updated_matches.append(rec)
            logs.append(f"validate_entity: skip (registry row missing {entity_id}).")
            continue

        contribs = run_mvr_validation(entity, mvr=registry._mvr)
        all_contribs.extend(contribs)
        if not logs:
            logs.append(
                "validate_entity: ran MVR validation on provisional registry row(s).",
            )
        for item in contribs:
            vc = item.get("validation_contrib") or {}
            logs.append(
                f"validate_entity: {item.get('agent')} "
                f"{vc.get('field')} -> {vc.get('status')}.",
            )

        if not validation_all_passed(contribs):
            any_failed = True
            updated_matches.append(rec)
            logs.append(
                f"validate_entity: failed ({validation_failure_summary(contribs)}).",
            )
            continue

        updated = registry.promote_validated(str(entity_id))
        updated_matches.append(registry_entity_to_match(updated, mvr=registry._mvr))

    if not processed_provisional:
        return {
            "validation_passed": None,
            "validation_contributions": [],
            "audit_log": ["validate_entity: skip (not provisional registry)."],
        }

    if len(matched) == 1 and any_failed:
        return {
            "matched_records": updated_matches,
            "validation_passed": False,
            "validation_contributions": all_contribs,
            "audit_log": logs,
        }

    result: dict[str, Any] = {
        "matched_records": updated_matches,
        "validation_contributions": all_contribs,
        "audit_log": logs + ["validate_entity: promoted to validated."],
        "validation_passed": None if any_failed else True,
    }

    if any_failed:
        result["audit_log"] = logs + [
            "validate_entity: batch has row(s) still provisional after validation.",
        ]

    if (
        not any_failed
        and graph_requested_attributes(current)
        and current.classifications
        and research_gate_allows(
            current_id=updated_matches[0].get("id")
            if len(updated_matches) == 1
            else None,
            matched=updated_matches,
        )
    ):
        specialists_to_invoke: list[str] = []
        audit: list[str] = []
        specialists_to_invoke = _collect_specialists_to_invoke(
            current.classifications,
            audit,
        )
        result["audit_log"] = list(result["audit_log"]) + audit
        if specialists_to_invoke:
            result["audit_log"].append(
                "validate_entity: validation passed — scheduling attribute specialists.",
            )
        ids = [str(m.get("id")) for m in updated_matches if m.get("id")]
        ctx = planner_context(
            matched=updated_matches[0]
            if len(updated_matches) == 1
            else updated_matches,
            ids=ids,
            specialists_to_invoke=specialists_to_invoke,
            contributions=list(_meta(current).get("contributions") or []),
        )
        if len(updated_matches) == 1:
            result["current_id"] = updated_matches[0].get("id")
        result["context"] = ctx

    return result


def build_context_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Pull entity + all specialist storage for matched id(s) into state.context."""
    current = _coerce(state)
    meta = _meta(current)
    ids = list(meta.get("ids") or [])
    if current.current_id and current.current_id not in ids:
        ids.append(current.current_id)

    builder = get_context_builder()
    full_ctx = builder.build_full_context(
        ids,
        matched_records=current.matched_records or None,
    )
    meta = dict(meta)
    meta.setdefault("specialists_to_invoke", [])
    meta.setdefault("contributions", [])

    merged: dict[str, Any] = {
        "entity_id": full_ctx.get("entity_id"),
        "bind": full_ctx.get("bind"),
        "specialists": full_ctx.get("specialists", {}),
        "_meta": meta,
    }
    n_cats = len(merged.get("specialists") or {})
    logs = [
        f"build_context: built context from {n_cats} specialist store(s) "
        f"for {len(ids)} id(s).",
    ]
    return {"context": merged, "audit_log": logs}


def _entity_ids_from_state(current: MyceliumGraphState) -> list[str]:
    """Return all entity ids scheduled for this graph turn (batch deliver safe)."""
    meta = _meta(current)
    ids = [str(entity_id) for entity_id in (meta.get("ids") or []) if entity_id]
    if ids:
        return ids
    if current.current_id:
        return [str(current.current_id)]
    matched = current.matched_records or []
    return [str(row["id"]) for row in matched if row.get("id")]


def _context_for_entity(
    ctx: dict[str, Any] | None,
    entity_id: str,
    matched_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Narrow planner/build context to one entity row (batch step-2 deliver)."""
    base = dict(ctx) if isinstance(ctx, dict) else {}
    row = next(
        (record for record in matched_records if str(record.get("id") or "") == entity_id),
        None,
    )
    base["entity_id"] = entity_id
    if row is not None:
        base["bind"] = bind_from_record(row)
    return base


def invoke_specialists_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Sequentially invoke each required specialist with full context + owned fields."""
    current = _coerce(state)
    if not research_gate_allows(
        current_id=current.current_id,
        matched=current.matched_records or [],
    ):
        return {
            "audit_log": ["invoke_specialists: blocked by research gate."],
            "route": None,
        }
    meta = _meta(current)
    to_invoke: list[str] = list(meta.get("specialists_to_invoke") or [])
    contributions: list[dict[str, Any]] = list(meta.get("contributions") or [])
    logs: list[str] = []
    registry = get_agent_registry()
    entity_ids = _entity_ids_from_state(current)
    matched = list(current.matched_records or [])
    base_ctx = current.context if isinstance(current.context, dict) else {}

    for entity_id in entity_ids:
        entity_ctx = _context_for_entity(base_ctx, entity_id, matched)
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
                    "context": entity_ctx,
                    "current_id": entity_id,
                    "target_fields": target_fields,
                    "route": agent_name,
                },
            )
            result = fn(enriched)
            contrib_audit = list(result.get("audit_log") or [])
            specialist_contrib = result.get("specialist_contrib") or {}
            researched_fields = list(specialist_contrib.get("researched_fields") or [])
            if not researched_fields:
                researched_fields = parse_research_fields_updated(contrib_audit)
            contributions.append(
                {
                    "agent": agent_name,
                    "entity_id": entity_id,
                    "target_fields": target_fields,
                    "specialist_contrib": specialist_contrib,
                    "response": result.get("response"),
                    "audit_log": contrib_audit,
                    "researched_fields": researched_fields,
                },
            )
            logs.append(
                f"invoke_specialists: invoked {agent_name} for id={entity_id!r} "
                f"({len(target_fields)} owned field(s)).",
            )
            if contrib_audit:
                logs.extend(contrib_audit)

    growth_logs: list[str] = []
    for entity_id in entity_ids:
        growth_logs.extend(
            apply_registry_research_attribution(
                entity_id=entity_id,
                contributions=contributions,
            ),
        )
    logs.extend(growth_logs)

    if current.metering_write_entitlement and current.metering_accepted_quote:
        researched_any = any(
            list((c.get("researched_fields") or []))
            for c in contributions
        )
        if researched_any:
            principal = current.query.principal
            sponsor_id = principal.id if principal is not None else None
            record = write_entitlement_from_accepted_quote(
                accepted_quote=current.metering_accepted_quote,
                sponsor_id=sponsor_id,
            )
            logs.append(
                f"invoke_specialists: wrote entitlement {record.entitlement_id}.",
            )

    meta = dict(meta)
    meta["contributions"] = contributions
    ctx = dict(current.context) if isinstance(current.context, dict) else {}
    ctx["_meta"] = meta
    return {"context": ctx, "audit_log": logs, "route": None}


def _attach_provenance(
    response: QueryResponse,
    state: MyceliumGraphState,
    matched: list[dict[str, Any]],
) -> QueryResponse:
    from agents.query_provenance import apply_query_provenance

    attrs = graph_requested_attributes(state)
    return apply_query_provenance(
        response,
        state.query,
        matched,
        requested_attributes=attrs,
        provenance=graph_provenance_requested(state),
    )


def _operator_audit_from_logs(audit_log: list[str] | None) -> list[str]:
    """Derive retry lines for QueryResponse.debug (MCP operator visibility)."""
    if not audit_log:
        return []
    return [line for line in audit_log if ": derive " in line]


def assemble_response_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Produce final QueryResponse from entity matches and specialist contributions."""
    current = _coerce(state)
    if current.response is not None:
        return {"audit_log": ["assemble_response: passthrough (preset response)."]}

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
    resolve_record_type = meta.get("resolve_record_type") or default_record_type()
    contributions = meta.get("contributions") or []
    matched = current.matched_records or []

    if current.metering_payment_required and current.pending_quote:
        identity_records = (
            _identity_records_from_match(matched, record_type=resolve_record_type)
            if matched
            else []
        )
        return {
            "response": response_payment_required(
                query,
                current.pending_quote,
                base_records=identity_records or None,
                **id_kwargs,
            ),
            "audit_log": ["assemble_response: payment_required."],
        }

    if current.pending_quote:
        identity_records = (
            _identity_records_from_match(matched, record_type=resolve_record_type)
            if matched
            else []
        )
        return {
            "response": response_quote_required(
                query,
                current.pending_quote,
                base_records=identity_records or None,
                **id_kwargs,
            ),
            "audit_log": ["assemble_response: quote_required."],
        }

    if current.metering_principal_required:
        return {
            "response": response_principal_required(
                query,
                funding_model=current.metering_principal_required,
                **id_kwargs,
            ),
            "audit_log": [
                "assemble_response: principal_required "
                f"({current.metering_principal_required}).",
            ],
        }

    if current.validation_passed is False and matched and len(matched) == 1:
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
        and not graph_requested_attributes(current)
    ):
        return {
            "response": response_found(
                query,
                base_records=_identity_records_from_match(
                    matched,
                    record_type=resolve_record_type,
                ),
                message="Core record validated.",
                **id_kwargs,
            ),
            "audit_log": ["assemble_response: entity validated."],
        }

    if is_research_gated(current):
        gated = response_research_gated(query, matched, **id_kwargs)
        return {
            "response": _attach_provenance(gated, current, matched),
            "audit_log": ["assemble_response: research gate (provisional + attrs)."],
        }

    if not matched:
        return {
            "response": response_not_found(query, **id_kwargs, **clf_kwargs),
            "audit_log": ["assemble_response: no entity match."],
        }

    requested = graph_requested_attributes(current)

    if not requested:
        identity_records = _identity_records_from_match(
            matched,
            record_type=resolve_record_type,
        )
        message = None
        if current.duplicate_bind and len(matched) == 1:
            label = _identity_message_label(matched[0], query=query)
            if matched[0].get("_validation_state") == "validated":
                message = f"Already bound record for {label}."
            else:
                message = f"Already bound provisional record for {label}."
        resp = response_found(
            query,
            base_records=identity_records,
            message=message,
            **id_kwargs,
            **clf_kwargs,
        )
        return {
            "response": _attach_provenance(resp, current, matched),
            "audit_log": ["assemble_response: entity identity response."],
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
    operator_audit = _operator_audit_from_logs(current.audit_log)
    if operator_audit:
        debug_extra["operator_audit"] = operator_audit

    resp = response_assembled(
        query,
        merged_records=merged_records,
        classifications=current.classifications or [],
        contributions=contributions,
        audit_log=current.audit_log,
        debug_extra=debug_extra,
        requested_attributes=requested,
        **id_kwargs,
    )
    if contributions:
        audit = "assemble_response: merged specialist contributions."
    else:
        audit = "assemble_response: requested attrs, no contributions."

    return {
        "response": _attach_provenance(resp, current, matched),
        "audit_log": [audit],
    }


# Legacy name used by older graph wiring (replaced by invoke_specialists_node).
def specialist_dispatcher(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return invoke_specialists_node(state)

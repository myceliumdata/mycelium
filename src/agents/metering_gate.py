"""Workload metering gate after entity validation (Slice 10)."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from agents.entity_registry import get_entity_registry
from models.state import BillingPrincipal, MyceliumGraphState, entity_query_is_delivery_step, graph_provenance_requested, graph_requested_attributes
from network.entitlements import EntitlementRecord, get_entitlement_store
from network.metering_policy import MeteringPolicy, load_metering_policy
from network.payment import payment_bypassed, settle_quote
from network.quotes import (
    BuiltinQuoteProvider,
    CacheState,
    WorkloadSpec,
    compute_scope_hash,
    get_quote_store,
    principal_required_error,
    quote_payload,
)

AcceptQuoteKind = Literal["accepted", "payment_required", "mismatch"]


@dataclass(frozen=True)
class AcceptQuoteResult:
    kind: AcceptQuoteKind
    accepted_quote: dict[str, Any] | None = None
    payment_quote: dict[str, Any] | None = None
    write_entitlement: bool = False


def accept_quote_for_workload(
    *,
    quote_id: str,
    workload: WorkloadSpec,
    cache_state: CacheState,
    policy: MeteringPolicy,
    principal: BillingPrincipal | None,
) -> AcceptQuoteResult:
    """Try to accept ``quote_id`` when its workload hash matches."""
    resolved_quote_id = quote_id.strip()
    if not resolved_quote_id:
        return AcceptQuoteResult(kind="mismatch")

    store = get_quote_store()
    stored = store.get(resolved_quote_id)
    if stored is None or stored.workload.scope_hash != workload.scope_hash:
        return AcceptQuoteResult(kind="mismatch")

    payment_policy = policy.payment
    require_paid = (
        payment_policy.enabled and payment_policy.require_paid_before_accept
    )
    if (
        require_paid
        and stored.status == "pending"
        and not payment_bypassed(payment_policy)
    ):
        return AcceptQuoteResult(
            kind="payment_required",
            payment_quote=quote_payload(stored),
        )
    if (
        require_paid
        and stored.status == "pending"
        and payment_bypassed(payment_policy)
    ):
        settle_quote(
            resolved_quote_id,
            principal=principal,
            provider_name=payment_policy.provider,
        )
    accepted = store.accept(
        resolved_quote_id,
        require_paid=require_paid and not payment_bypassed(payment_policy),
    )
    if accepted is None:
        return AcceptQuoteResult(kind="mismatch")

    write_production = cache_state in {"miss", "partial"}
    return AcceptQuoteResult(
        kind="accepted",
        accepted_quote=quote_payload(accepted),
        write_entitlement=write_production,
    )


def auto_accept_quotes_enabled() -> bool:
    return os.getenv("MYCELIUM_AUTO_ACCEPT_QUOTES", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def metering_bypassed(policy: MeteringPolicy) -> bool:
    return not policy.enabled or auto_accept_quotes_enabled()


def build_workload_spec(state: MyceliumGraphState) -> WorkloadSpec | None:
    entity_id = state.current_id
    if not entity_id:
        matched = state.matched_records or []
        if len(matched) == 1 and matched[0].get("id"):
            entity_id = str(matched[0]["id"])
    requested = graph_requested_attributes(state)
    if not entity_id or not requested:
        return None
    workload = WorkloadSpec(
        entity_id=entity_id,
        requested_attributes=requested,
        provenance=graph_provenance_requested(state),
    )
    return workload.model_copy(update={"scope_hash": compute_scope_hash(workload)})


def resolve_cache_state(
    workload: WorkloadSpec,
    *,
    requested_attributes: list[str],
) -> CacheState:
    entitlements = get_entitlement_store()
    if entitlements.lookup_by_scope_hash(workload.scope_hash) is not None:
        return "hit"

    registry = get_entity_registry()
    entity = registry.lookup_by_id(workload.entity_id)
    if entity is None:
        return "miss"

    researched = {
        attr.strip().lower()
        for attr in entity.last_researched_at.keys()
        if attr.strip()
    }
    needed = {attr.strip().lower() for attr in requested_attributes if attr.strip()}
    if needed and needed.issubset(researched):
        return "hit"
    if researched & needed:
        return "partial"
    return "miss"


def should_meter(state: MyceliumGraphState) -> bool:
    if not graph_requested_attributes(state):
        return False
    if state.entity_resolution_kind in {"unknown", "under_specified", "suggest"}:
        return False
    if state.validation_passed is False:
        return False
    from agents.research_gate import is_research_gated

    if is_research_gated(state):
        return False
    return True


def write_entitlement_from_accepted_quote(
    *,
    accepted_quote: dict[str, Any],
    sponsor_id: str | None = None,
) -> EntitlementRecord:
    workload = WorkloadSpec.model_validate(accepted_quote["workload"])
    offer = accepted_quote.get("entitlement_offer") or {}
    entitlement_id = str(offer.get("entitlement_id") or f"ent_{uuid.uuid4().hex[:12]}")
    record = EntitlementRecord(
        entitlement_id=entitlement_id,
        scope_hash=workload.scope_hash,
        sponsor_id=sponsor_id or offer.get("sponsor_id"),
        funded_line_items=list(offer.get("covers") or ["production"]),
    )
    get_entitlement_store().write(record)
    return record


def metering_gate_node(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    from agents.dispatch import _coerce

    current = _coerce(state)
    policy = load_metering_policy()
    if (
        entity_query_is_delivery_step(current.query)
        and current.metering_accepted_quote
    ):
        return {
            "pending_quote": None,
            "audit_log": ["metering_gate: target deliver quote already accepted."],
        }
    if metering_bypassed(policy) or not should_meter(current):
        return {
            "pending_quote": None,
            "audit_log": ["metering_gate: bypassed or not billable."],
        }

    workload = build_workload_spec(current)
    if workload is None:
        return {"pending_quote": None, "audit_log": ["metering_gate: no workload."]}

    cache_state = resolve_cache_state(
        workload,
        requested_attributes=workload.requested_attributes,
    )
    funding_model = policy.default_funding_model
    principal = current.query.principal
    principal_err = principal_required_error(funding_model, policy, principal)
    if principal_err:
        return {
            "pending_quote": None,
            "audit_log": [f"metering_gate: {principal_err}"],
            "metering_principal_required": funding_model,
        }

    provider = BuiltinQuoteProvider()
    quote = provider.quote(
        workload=workload,
        cache_state=cache_state,
        funding_model=funding_model,
        policy=policy,
        principal=principal,
    )

    if quote.total_usd <= 0:
        return {
            "pending_quote": None,
            "audit_log": ["metering_gate: zero-cost quote — proceed."],
        }

    store = get_quote_store()
    if current.query.quote_id:
        accepted_result = accept_quote_for_workload(
            quote_id=current.query.quote_id,
            workload=workload,
            cache_state=cache_state,
            policy=policy,
            principal=principal,
        )
        if accepted_result.kind == "payment_required" and accepted_result.payment_quote:
            return {
                "pending_quote": accepted_result.payment_quote,
                "metering_payment_required": True,
                "audit_log": [
                    f"metering_gate: payment_required {current.query.quote_id}.",
                ],
            }
        if accepted_result.kind == "accepted" and accepted_result.accepted_quote:
            return {
                "pending_quote": None,
                "metering_payment_required": False,
                "metering_accepted_quote": accepted_result.accepted_quote,
                "metering_write_entitlement": accepted_result.write_entitlement,
                "audit_log": [
                    f"metering_gate: accepted quote {current.query.quote_id}.",
                ],
            }

    issued = store.issue(quote)
    return {
        "pending_quote": quote_payload(issued),
        "metering_payment_required": False,
        "audit_log": [f"metering_gate: quote_required {issued.quote_id}."],
    }

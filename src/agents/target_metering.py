"""Target-protocol metering for step-1 resolve and step-2 deliver (MVR redesign M6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from agents.metering_gate import (
    accept_quote_for_workload,
    metering_bypassed,
    resolve_cache_state,
)
from models.state import BillingPrincipal, DeliveryPayload, EntityQuery, normalized_requested_attributes
from network.delivery import DeliveryScope
from network.metering_policy import MeteringPolicy, load_metering_policy
from network.quotes import (
    BuiltinQuoteProvider,
    CacheState,
    Quote,
    WorkloadSpec,
    compute_scope_hash,
    get_quote_store,
    principal_required_error,
    quote_payload,
)

TargetMeteringKind = Literal[
    "free",
    "quote_required",
    "payment_required",
    "principal_required",
    "accepted",
]


@dataclass(frozen=True)
class TargetMeteringResult:
    kind: TargetMeteringKind
    quote: dict[str, Any] | None = None
    accepted_quote: dict[str, Any] | None = None
    write_entitlement: bool = False
    funding_model: str | None = None
    cache_state: CacheState | None = None


def workload_from_delivery_scope(scope: DeliveryScope) -> WorkloadSpec:
    attrs = normalized_requested_attributes(scope.requested_attributes)
    workload = WorkloadSpec(
        delivery_id=scope.delivery_id,
        entity_ids=list(scope.entity_ids),
        entity_id=scope.entity_ids[0] if len(scope.entity_ids) == 1 else "",
        requested_attributes=attrs,
        provenance=bool(scope.provenance),
        create_on_deliver=bool(scope.create_on_deliver),
    )
    return workload.model_copy(update={"scope_hash": compute_scope_hash(workload)})


def resolve_batch_cache_state(workload: WorkloadSpec) -> CacheState:
    """Aggregate cache state across delivery scope entities (worst-case wins)."""
    from network.entitlements import get_entitlement_store

    entitlements = get_entitlement_store()
    if entitlements.lookup_by_scope_hash(workload.scope_hash) is not None:
        return "hit"

    entity_ids = list(workload.entity_ids)
    if not entity_ids and workload.entity_id:
        entity_ids = [workload.entity_id]
    if not entity_ids:
        return "miss"

    attrs = list(workload.requested_attributes)
    states: list[CacheState] = []
    for entity_id in entity_ids:
        single = WorkloadSpec(
            entity_id=entity_id,
            requested_attributes=attrs,
            provenance=workload.provenance,
        )
        single = single.model_copy(update={"scope_hash": compute_scope_hash(single)})
        states.append(resolve_cache_state(single, requested_attributes=attrs))

    if "miss" in states:
        return "miss"
    if "partial" in states:
        return "partial"
    return "hit"


def step1_should_quote(scope: DeliveryScope, policy: MeteringPolicy) -> bool:
    """Step-1 quotes when metering is on and attrs/provenance workload is billable."""
    if metering_bypassed(policy):
        return False
    return bool(normalized_requested_attributes(scope.requested_attributes)) or scope.provenance


def step2_should_quote(policy: MeteringPolicy) -> bool:
    return not metering_bypassed(policy)


def run_target_metering_gate(
    *,
    query: EntityQuery,
    scope: DeliveryScope,
    quote_id: str | None = None,
    principal: BillingPrincipal | None = None,
    require_quote: bool,
) -> TargetMeteringResult:
    """Issue or accept a quote bound to ``delivery_id`` workload."""
    policy = load_metering_policy()
    if not require_quote or metering_bypassed(policy):
        return TargetMeteringResult(kind="free")

    workload = workload_from_delivery_scope(scope)
    cache_state = resolve_batch_cache_state(workload)
    funding_model = policy.default_funding_model
    principal_err = principal_required_error(funding_model, policy, principal)
    if principal_err:
        return TargetMeteringResult(
            kind="principal_required",
            funding_model=funding_model,
            cache_state=cache_state,
        )

    provider = BuiltinQuoteProvider()
    quote = provider.quote(
        workload=workload,
        cache_state=cache_state,
        funding_model=funding_model,
        policy=policy,
        principal=principal,
    )

    if quote.total_usd <= 0:
        return TargetMeteringResult(kind="free", cache_state=cache_state)

    store = get_quote_store()
    resolved_quote_id = (quote_id or query.quote_id or "").strip()
    if resolved_quote_id:
        accepted_result = accept_quote_for_workload(
            quote_id=resolved_quote_id,
            workload=workload,
            cache_state=cache_state,
            policy=policy,
            principal=principal,
        )
        if accepted_result.kind == "payment_required" and accepted_result.payment_quote:
            return TargetMeteringResult(
                kind="payment_required",
                quote=accepted_result.payment_quote,
                cache_state=cache_state,
            )
        if accepted_result.kind == "accepted" and accepted_result.accepted_quote:
            return TargetMeteringResult(
                kind="accepted",
                accepted_quote=accepted_result.accepted_quote,
                write_entitlement=accepted_result.write_entitlement,
                cache_state=cache_state,
            )

    issued = store.issue(quote)
    return TargetMeteringResult(
        kind="quote_required",
        quote=_quote_payload_with_delivery(issued, scope),
        cache_state=cache_state,
    )


def _quote_payload_with_delivery(quote: Quote, scope: DeliveryScope) -> dict[str, Any]:
    payload = quote_payload(quote)
    workload = dict(payload.get("workload") or {})
    workload["delivery_id"] = scope.delivery_id
    workload["entity_ids"] = list(scope.entity_ids)
    payload["workload"] = workload
    return payload


def delivery_payload_from_scope(scope: DeliveryScope) -> DeliveryPayload:
    return DeliveryPayload.from_scope(scope)

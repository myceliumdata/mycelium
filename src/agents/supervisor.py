"""Supervisor: classification and specialist invocation planning for step-2 deliver."""

from __future__ import annotations

from typing import Any

from agents.classification import get_category_tree
from agents.context import planner_context
from agents.factory.agent_factory import get_agent_factory
from agents.registry import get_agent_registry
from agents.research_gate import research_gate_allows
from models.state import (
    MyceliumGraphState,
    entity_query_is_delivery_step,
    graph_requested_attributes,
)

# Context pull + specialist calls run in graph nodes (build_context, invoke_specialists).
# TODO: peer retrieval replaces supervisor-provided full context union.


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _short_circuit_context() -> dict[str, Any]:
    return planner_context(matched=[], ids=[], specialists_to_invoke=[])


def _collect_specialists_to_invoke(
    classifications: list[dict[str, Any]],
    audit_log: list[str],
) -> list[str]:
    """Unique assigned agents for known categories (create on demand if missing)."""
    reg = get_agent_registry()
    factory = get_agent_factory()
    ordered: list[str] = []
    seen: set[str] = set()

    for cl in classifications:
        cat = cl.get("category")
        ag = cl.get("assigned_agent")
        if not cat or cat == "unknown" or not ag or ag in seen:
            continue
        seen.add(ag)
        if not reg.has_agent(ag):
            factory.create_specialist(
                category=cat,
                agent_name=ag,
                description=cl.get("description") or f"Data related to {cat}.",
                examples=[],
                llm_refine=False,
                auto_commit=False,
            )
            audit_log.append(
                f"Supervisor: created new specialist {ag} for category {cat}.",
            )
        ordered.append(ag)

    return ordered


def _classify_requested_attributes(
    query,
    audit_log: list[str],
    *,
    attributes: list[str] | None = None,
) -> list[dict[str, Any]]:
    attrs = attributes if attributes is not None else query.requested_attributes
    if not attrs:
        return []
    tree = get_category_tree()
    classifications: list[dict[str, Any]] = []
    for attr in attrs:
        cl = tree.classify(attr)
        classifications.append(cl.model_dump())
        if cl.category != "unknown":
            audit_log.append(
                f"Supervisor: classified '{attr}' -> category={cl.category}, "
                f"agent={cl.assigned_agent}, confidence={cl.confidence:.2f}",
            )
    return classifications


def _target_fields_for_agent(
    agent_name: str,
    classifications: list[dict[str, Any]],
) -> list[str]:
    fields: list[str] = []
    for cl in classifications:
        if cl.get("assigned_agent") == agent_name and cl.get("attribute"):
            fields.append(cl["attribute"])
    return fields


def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Classify requested attributes and plan specialists for step-2 deliver.

    Step-1 resolve terminates in ``target_resolve_node``. This node only runs when
    ``target_resolve`` hydrated ``matched_records`` for a delivery scope.
    """
    current = _coerce(state)
    query = current.query
    audit_log = ["Supervisor: evaluating query."]

    if entity_query_is_delivery_step(query) and current.matched_records:
        matched = current.matched_records
        audit_log.append(
            f"Supervisor: step-2 deliver — using {len(matched)} scope entity row(s).",
        )
        ids = [m["id"] for m in matched if m.get("id")]
        attrs = graph_requested_attributes(current)
        classifications = _classify_requested_attributes(
            query,
            audit_log,
            attributes=attrs,
        )
        specialists_to_invoke: list[str] = []
        if research_gate_allows(current_id=None, matched=matched):
            specialists_to_invoke = _collect_specialists_to_invoke(
                classifications,
                audit_log,
            )
            if specialists_to_invoke:
                audit_log.append(
                    f"Supervisor: will invoke specialist(s): "
                    f"{', '.join(specialists_to_invoke)}.",
                )
        context = planner_context(
            matched=matched[0] if len(matched) == 1 else matched,
            ids=ids,
            specialists_to_invoke=specialists_to_invoke,
        )
        result: dict[str, Any] = {
            "matched_records": matched,
            "entity_resolution_kind": "exact",
            "entity_suggestions": [],
            "context": context,
            "audit_log": audit_log,
            "route": None,
        }
        if classifications:
            result["classifications"] = classifications
        if len(matched) == 1:
            result["current_id"] = matched[0]["id"]
        return result

    audit_log.append(
        "Supervisor: no delivery scope — step 1 should terminate in target_resolve.",
    )
    return {
        "matched_records": [],
        "entity_resolution_kind": "none",
        "entity_suggestions": [],
        "context": _short_circuit_context(),
        "audit_log": audit_log,
        "route": None,
    }

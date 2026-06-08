"""Supervisor: seed resolution, classification, and specialist invocation planning."""

from __future__ import annotations

from typing import Any

from agents.classification import get_category_tree
from agents.factory.agent_factory import get_agent_factory
from agents.registry import get_agent_registry
from agents.seed import find_by_key
from models.state import MyceliumGraphState, Person

# Context pull + specialist calls run in graph nodes (build_context, invoke_specialists).
# TODO: peer retrieval replaces supervisor-provided full context union.


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _identity_records_from_seed(matched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build public result dicts; ``id`` is the seed-loader UUID."""
    records: list[dict[str, Any]] = []
    for rec in matched:
        pid = rec.get("id", "")
        records.append(
            {
                "id": pid,
                "name": rec.get("name", ""),
                "employer": rec.get("employer"),
            },
        )
    return records


def _persons_from_seed(matched: list[dict[str, Any]]) -> list[Person]:
    return [
        Person(
            id=rec.get("id", ""),
            name=rec.get("name", ""),
            employer=rec.get("employer"),
        )
        for rec in matched
    ]


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
    Resolve from seed, classify requested attributes, plan specialist invocations.

    Does not build the full cross-specialist context or final PersonResponse —
    graph nodes ``build_context``, ``invoke_specialists``, and ``assemble_response``
    handle those steps.
    """
    current = _coerce(state)
    query = current.query
    audit_log = ["Supervisor: evaluating query."]

    matched = find_by_key(query.person_key)
    persons = _persons_from_seed(matched)
    ids = [m["id"] for m in matched if m.get("id")]

    if matched:
        audit_log.append(
            f"Supervisor: resolved via seed, match count={len(matched)} "
            f"for {query.person_key!r}.",
        )
    else:
        audit_log.append(f"Supervisor: no seed match for {query.person_key!r}.")

    classifications: list[dict[str, Any]] = []
    if query.requested_attributes:
        tree = get_category_tree()
        for attr in query.requested_attributes:
            cl = tree.classify(attr)
            classifications.append(cl.model_dump())
            if cl.category != "unknown":
                audit_log.append(
                    f"Supervisor: classified '{attr}' -> category={cl.category}, "
                    f"agent={cl.assigned_agent}, confidence={cl.confidence:.2f}",
                )

    specialists_to_invoke = _collect_specialists_to_invoke(classifications, audit_log)
    if specialists_to_invoke:
        audit_log.append(
            f"Supervisor: will invoke specialist(s): {', '.join(specialists_to_invoke)}.",
        )

    context: dict[str, Any] = {
        "seed": matched[0] if len(matched) == 1 else matched,
        "specialists": {},
        "_meta": {
            "ids": ids,
            "specialists_to_invoke": specialists_to_invoke,
            "contributions": [],
        },
    }

    result: dict[str, Any] = {
        "matched_persons": matched,
        "context": context,
        "audit_log": audit_log,
        "route": None,
    }
    if classifications:
        result["classifications"] = classifications
    if len(matched) == 1:
        result["current_id"] = matched[0]["id"]
    if persons:
        result["persons"] = persons
        if len(persons) == 1:
            result["person"] = persons[0]

    return result

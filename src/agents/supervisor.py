"""Supervisor: entity resolution, classification, and specialist invocation planning."""

from __future__ import annotations

from typing import Any

from agents.classification import get_category_tree
from agents.entity_resolution import is_provisional_registry_match, resolve_entity
from agents.factory.agent_factory import get_agent_factory
from agents.registry import get_agent_registry
from models.state import MyceliumGraphState, SeedRecord

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


def _seed_records_from_seed(matched: list[dict[str, Any]]) -> list[SeedRecord]:
    return [
        SeedRecord(
            id=rec.get("id", ""),
            name=rec.get("name", ""),
            employer=rec.get("employer"),
        )
        for rec in matched
    ]


def _short_circuit_context() -> dict[str, Any]:
    return {
        "seed": [],
        "specialists": {},
        "_meta": {
            "ids": [],
            "specialists_to_invoke": [],
            "contributions": [],
        },
    }


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
) -> list[dict[str, Any]]:
    if not query.requested_attributes:
        return []
    tree = get_category_tree()
    classifications: list[dict[str, Any]] = []
    for attr in query.requested_attributes:
        cl = tree.classify(attr)
        classifications.append(cl.model_dump())
        if cl.category != "unknown":
            audit_log.append(
                f"Supervisor: classified '{attr}' -> category={cl.category}, "
                f"agent={cl.assigned_agent}, confidence={cl.confidence:.2f}",
            )
    return classifications


def _research_allowed(matched: list[dict[str, Any]]) -> bool:
    """Seed matches or validated registry rows may invoke attribute specialists."""
    if not matched:
        return False
    if len(matched) != 1:
        return not matched[0].get("_registry")
    rec = matched[0]
    if rec.get("_registry"):
        return rec.get("_validation_state") == "validated"
    return True


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
    Resolve entity (registry + seed), classify requested attributes, plan specialists.

    Does not build the full cross-specialist context or final QueryResponse —
    graph nodes ``build_context``, ``invoke_specialists``, and ``assemble_response``
    handle those steps.
    """
    current = _coerce(state)
    query = current.query
    audit_log = ["Supervisor: evaluating query."]

    resolution = resolve_entity(query)

    if resolution.kind == "suggest":
        audit_log.append(
            f"Supervisor: near-miss suggestions for {query.entity_key!r} "
            f"(count={len(resolution.suggestions)}); skipping classification.",
        )
        return {
            "matched_records": [],
            "entity_resolution_kind": "suggest",
            "entity_suggestions": resolution.suggestions,
            "context": _short_circuit_context(),
            "audit_log": audit_log,
            "route": None,
        }

    if resolution.kind == "unknown":
        audit_log.append(
            f"Supervisor: unknown entity {query.entity_key!r}; "
            "skipping classification and specialists.",
        )
        return {
            "matched_records": [],
            "entity_resolution_kind": "unknown",
            "entity_required_fields": resolution.required_fields,
            "entity_suggestions": [],
            "context": _short_circuit_context(),
            "audit_log": audit_log,
            "route": None,
        }

    if resolution.kind == "under_specified":
        audit_log.append(
            f"Supervisor: under-specified bind for {query.entity_key!r}; "
            "skipping classification and specialists.",
        )
        return {
            "matched_records": [],
            "entity_resolution_kind": "under_specified",
            "entity_required_fields": resolution.required_fields,
            "entity_suggestions": [],
            "context": _short_circuit_context(),
            "audit_log": audit_log,
            "route": None,
        }

    if resolution.kind == "bind_provisional":
        matched = resolution.matches
        audit_log.append(
            f"Supervisor: provisional bind for {query.entity_key!r} "
            f"(id={matched[0].get('id')!r}); validation runs next.",
        )
        classifications = _classify_requested_attributes(query, audit_log)
        result: dict[str, Any] = {
            "matched_records": matched,
            "entity_resolution_kind": "bind_provisional",
            "entity_suggestions": [],
            "current_id": matched[0].get("id"),
            "context": {
                "seed": matched[0],
                "specialists": {},
                "_meta": {
                    "ids": [matched[0].get("id", "")],
                    "specialists_to_invoke": [],
                    "contributions": [],
                },
            },
            "audit_log": audit_log,
            "route": None,
        }
        if classifications:
            result["classifications"] = classifications
        return result

    matched = resolution.matches
    seed_records = _seed_records_from_seed(matched)
    ids = [m["id"] for m in matched if m.get("id")]
    if matched:
        source = "registry" if matched[0].get("_registry") else "seed"
        audit_log.append(
            f"Supervisor: resolved via {source}, match count={len(matched)} "
            f"for {query.entity_key!r}.",
        )
        if resolution.duplicate_bind:
            audit_log.append("Supervisor: duplicate bind key — existing entity returned.")
    else:
        audit_log.append(f"Supervisor: no match for {query.entity_key!r}.")

    classifications = _classify_requested_attributes(query, audit_log)
    specialists_to_invoke: list[str] = []
    if _research_allowed(matched):
        specialists_to_invoke = _collect_specialists_to_invoke(
            classifications,
            audit_log,
        )
        if specialists_to_invoke:
            audit_log.append(
                f"Supervisor: will invoke specialist(s): "
                f"{', '.join(specialists_to_invoke)}.",
            )
    elif (
        len(matched) == 1
        and is_provisional_registry_match(matched[0])
        and query.requested_attributes
    ):
        audit_log.append(
            "Supervisor: provisional registry entity — defer specialists until "
            "validation.",
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
        "matched_records": matched,
        "entity_resolution_kind": resolution.kind if matched else "none",
        "entity_suggestions": [],
        "duplicate_bind": resolution.duplicate_bind,
        "context": context,
        "audit_log": audit_log,
        "route": None,
    }
    if classifications:
        result["classifications"] = classifications
    if len(matched) == 1:
        result["current_id"] = matched[0]["id"]
    if seed_records:
        result["seed_records"] = seed_records
        if len(seed_records) == 1:
            result["seed_record"] = seed_records[0]

    return result

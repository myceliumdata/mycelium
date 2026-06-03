"""Supervisor agent: coordinator and router for core lookups and specialist handoff."""

from __future__ import annotations

from typing import Any

from agents.classification import get_category_tree
from agents.factory.agent_factory import get_agent_factory
from agents.registry import get_agent_registry
from models.state import MyceliumGraphState


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Coordinator entry point: classify requested attributes and route to specialists.

    Does not access storage or build ``PersonResponse`` payloads. Lookups are
    delegated via ``route`` to the registered specialist (``core_data`` or generated).
    """
    current = _coerce(state)
    query = current.query
    audit_log = ["Supervisor: evaluating query."]

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

    # Phase 2: use classification to pick a real specialist. Create on demand if needed.
    route = "core_data"
    if classifications:
        for cl in classifications:
            cat = cl.get("category")
            ag = cl.get("assigned_agent")
            if cat and cat != "unknown" and ag and ag != "core_data":
                reg = get_agent_registry()
                if not reg.has_agent(ag):
                    factory = get_agent_factory()
                    factory.create_specialist(
                        category=cat,
                        agent_name=ag,
                        description=cl.get("description") or f"Data related to {cat}.",
                        examples=[],
                        llm_refine=False,
                    )
                    audit_log.append(
                        f"Supervisor: created new specialist {ag} for category {cat}.",
                    )
                route = ag
                break

    audit_log.append(f"Supervisor: routing to {route} specialist.")

    result: dict[str, Any] = {
        "route": route,
        "audit_log": audit_log,
    }
    if classifications:
        result["classifications"] = classifications

    return result

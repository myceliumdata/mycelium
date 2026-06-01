"""Enrich agent: ingests minimum viable core person data."""

from __future__ import annotations

from typing import Any

from agents.orchestrator import ensure_person_id
from models.state import MyceliumGraphState
from storage.core import get_storage


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def enrich_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Persist provided core person data."""
    current = _coerce(state)
    storage = get_storage()

    raw_person = current.person or current.query.provided_data
    if raw_person is None:
        return {
            "validation_passed": False,
            "validation_errors": ["EnrichAgent: no person payload to ingest."],
            "audit_log": ["EnrichAgent: aborted — missing person payload."],
        }

    person = ensure_person_id(raw_person)
    storage.upsert_person(person)

    return {
        "person": person,
        "audit_log": [f"EnrichAgent: upserted core person {person.id}."],
    }

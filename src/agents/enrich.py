"""Enrich agent: ingests minimum viable person data and stub enrichment."""

from __future__ import annotations

from typing import Any

from agents.orchestrator import ensure_person_id
from models.state import MyceliumGraphState, Person
from storage.core import get_storage


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def enrich_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Persist provided person data and apply Phase 1 enrichment stubs."""
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
    storage.store_embedding_stub(person.id)

    derivative = current.derivative
    if derivative is not None:
        stub_values = {attr: None for attr in derivative.attributes}
        storage.upsert_derivative_record(
            dataset_id=derivative.dataset_id,
            person_id=person.id,
            data=stub_values,
        )

    logs = [
        f"EnrichAgent: upserted person {person.id}.",
        "EnrichAgent: embedding stub stored (vector search not enabled).",
    ]
    if derivative:
        logs.append(
            f"EnrichAgent: derivative stub populated for dataset {derivative.dataset_id}.",
        )

    return {
        "person": person,
        "audit_log": logs,
    }

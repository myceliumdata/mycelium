"""Supervisor agent: coordinates core lookup, ingest routing, and specialist handoff."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from models.state import (
    MINIMUM_VIABLE_FIELDS,
    MyceliumGraphState,
    Person,
    PersonResponse,
    non_core_attributes,
)
from storage.core import get_storage


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Main supervisor logic:
    - Found person + core attrs → return data
    - Missing person + no provided_data → structured data_request
    - Missing person + provided_data → route to enrich
    - Non-core attributes → specialist_required (deferred_attributes; no core registry)
    """
    current = _coerce(state)
    storage = get_storage()
    query = current.query
    logs: list[str] = ["Supervisor: evaluating query."]

    if current.validation_passed is False:
        response = PersonResponse(
            status="validation_failed",
            person=current.person,
            errors=list(current.validation_errors),
            message="Validation failed for person record.",
        )
        logs.append("Supervisor: validation failed — finishing.")
        return {"response": response, "route": "finish", "audit_log": logs}

    if current.validation_passed is True and current.person is not None:
        response = PersonResponse(
            status="ingested",
            person=current.person,
            data=current.person.core_dict(),
            message="Person ingested and validated successfully.",
        )
        logs.append("Supervisor: post-validation ingest complete.")
        return {"response": response, "route": "finish", "audit_log": logs}

    if query.provided_data is not None:
        logs.append("Supervisor: provided_data present — routing to enrich.")
        return {
            "person": query.provided_data,
            "route": "enrich",
            "audit_log": logs,
        }

    person = storage.find_person(query.person_key)
    if person is None:
        from models.state import DataRequest

        response = PersonResponse(
            status="data_request",
            data_request=DataRequest(
                person_key=query.person_key,
                required_fields=list(MINIMUM_VIABLE_FIELDS),
            ),
            message="Person not found in core CRM storage.",
        )
        logs.append("Supervisor: person missing — returning data_request.")
        return {
            "response": response,
            "route": "finish",
            "audit_log": logs,
        }

    deferred = non_core_attributes(query.requested_attributes)
    if deferred:
        logs.append(
            f"Supervisor: non-core attributes require specialist routing: {', '.join(deferred)}.",
        )
        response = PersonResponse(
            status="specialist_required",
            person=person,
            data=person.core_dict(),
            deferred_attributes=deferred,
            message=(
                "Core person found. Requested attributes are not in core storage; "
                "specialist agent routing is not yet implemented."
            ),
        )
        return {
            "person": person,
            "response": response,
            "route": "finish",
            "audit_log": logs,
        }

    response = PersonResponse(
        status="found",
        person=person,
        data=person.core_dict(),
        message="Person found in core storage.",
    )
    logs.append(f"Supervisor: returning core data for {person.id}.")
    return {
        "person": person,
        "response": response,
        "route": "finish",
        "audit_log": logs,
    }


def ensure_person_id(person: Person) -> Person:
    """Assign a stable id when ingesting new records."""
    if person.id:
        return person
    slug = person.name.lower().replace(" ", "-")
    return person.model_copy(update={"id": f"person-{slug}-{uuid4().hex[:6]}"})

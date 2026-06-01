"""Orchestrator agent: routes lookups, ingest requests, and derivative datasets."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from models.state import (
    MINIMUM_VIABLE_FIELDS,
    MyceliumGraphState,
    Person,
    PersonResponse,
    attributes_requiring_derivative,
)
from storage.core import get_storage


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def orchestrator_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Main supervisor logic:
    - Found person + core attrs → return data
    - Missing person + no provided_data → structured data_request
    - Missing person + provided_data → route to enrich
    - Extra attributes → create derivative dataset stub
    """
    current = _coerce(state)
    storage = get_storage()
    query = current.query
    logs: list[str] = ["Orchestrator: evaluating query."]

    if current.validation_passed is False:
        response = PersonResponse(
            status="validation_failed",
            person=current.person,
            errors=list(current.validation_errors),
            message="Validation failed for person record.",
        )
        logs.append("Orchestrator: validation failed — finishing.")
        return {"response": response, "route": "finish", "audit_log": logs}

    if current.validation_passed is True and current.person is not None:
        response = PersonResponse(
            status="ingested",
            person=current.person,
            data=current.person.core_dict(),
            message="Person ingested and validated successfully.",
        )
        logs.append("Orchestrator: post-validation ingest complete.")
        return {"response": response, "route": "finish", "audit_log": logs}

    if query.provided_data is not None:
        logs.append("Orchestrator: provided_data present — routing to enrich.")
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
        logs.append("Orchestrator: person missing — returning data_request.")
        return {
            "response": response,
            "route": "finish",
            "audit_log": logs,
        }

    derivative_attrs = attributes_requiring_derivative(query.requested_attributes)
    if derivative_attrs:
        dataset_name = f"derivative-{person.id}-{'-'.join(derivative_attrs[:3])}"
        derivative = storage.create_derivative_dataset(
            name=dataset_name,
            attributes=derivative_attrs,
        )
        storage.stub_activate_derivative(derivative.dataset_id)
        logs.append(
            f"Orchestrator: derivative dataset stub created ({derivative.dataset_id}).",
        )
        response = PersonResponse(
            status="derivative_pending",
            person=person,
            data=person.core_dict(),
            derivative=derivative,
            message=(
                "Core person found. Derivative dataset stub created for "
                f"attributes: {', '.join(derivative_attrs)}."
            ),
        )
        return {
            "person": person,
            "derivative": derivative,
            "response": response,
            "route": "finish",
            "audit_log": logs,
        }

    extra = {attr: person.extra.get(attr) for attr in query.requested_attributes if attr in person.extra}
    response = PersonResponse(
        status="found",
        person=person,
        data={**person.core_dict(), **extra},
        message="Person found in core storage.",
    )
    logs.append(f"Orchestrator: returning core data for {person.id}.")
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
    slug = (person.email or person.name).lower().replace(" ", "-").replace("@", "-at-")
    return person.model_copy(update={"id": f"person-{slug}-{uuid4().hex[:6]}"})

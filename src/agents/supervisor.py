"""Supervisor agent: coordinates core lookup, ingest routing, and specialist handoff."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from models.state import (
    MINIMUM_VIABLE_FIELDS,
    MyceliumGraphState,
    Person,
    PersonQuery,
    PersonResponse,
    non_core_attributes,
)
from storage.core import get_storage


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _debug_for_query(query: PersonQuery, **extra: str) -> str:
    parts = [
        f"person_key={query.person_key!r}",
        f"requested_attributes={query.requested_attributes!r}",
    ]
    parts.extend(f"{key}={value!r}" for key, value in extra.items())
    return "; ".join(parts)


def _ingest_guidance_message(person_key: str) -> str:
    required = ", ".join(MINIMUM_VIABLE_FIELDS)
    return (
        f"No core record found for {person_key!r}. "
        f"This lookup did not match anyone in core storage. "
        f"If you need to add a new person, include {required} in provided_data "
        f"(MCP submit_person_data or CLI ingest)."
    )


def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Main supervisor logic:
    - Post-validation → ingest success or failure response
    - provided_data (first pass) → route to enrich
    - Found person + core attrs → results + narrative message
    - Missing person → empty results + ingest guidance in message
    - Non-core attributes → core record in results, researching narrative in message
    """
    current = _coerce(state)
    storage = get_storage()
    query = current.query
    logs: list[str] = ["Supervisor: evaluating query."]

    if current.validation_passed is False:
        error_summary = "; ".join(current.validation_errors) or "unknown validation errors"
        response = PersonResponse(
            results=[],
            message=f"Could not add core record: {error_summary}",
            debug=_debug_for_query(query, outcome="ingest_failed", errors=error_summary),
        )
        logs.append("Supervisor: validation failed — finishing.")
        return {"response": response, "route": "finish", "audit_log": logs}

    if current.validation_passed is True and current.person is not None:
        person = current.person
        storage.upsert_person(person)
        response = PersonResponse(
            results=[person.core_dict()],
            message=f"Added core record for {person.name}.",
            debug=_debug_for_query(query, outcome="ingested"),
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
        required = ", ".join(MINIMUM_VIABLE_FIELDS)
        response = PersonResponse(
            results=[],
            message=_ingest_guidance_message(query.person_key),
            debug=_debug_for_query(
                query,
                outcome="ingest_required",
                required_fields=required,
            ),
        )
        logs.append("Supervisor: person missing — returning ingest guidance.")
        return {
            "response": response,
            "route": "finish",
            "audit_log": logs,
        }

    deferred = non_core_attributes(query.requested_attributes)
    if deferred:
        attr_list = ", ".join(deferred)
        logs.append(
            f"Supervisor: non-core attributes require specialist routing: {attr_list}.",
        )
        response = PersonResponse(
            results=[person.core_dict()],
            message=(
                f"We have a core record for {person.name}, but we're still researching "
                f"{attr_list}."
            ),
            debug=_debug_for_query(
                query,
                outcome="non_core_requested",
                deferred_attributes=attr_list,
            ),
        )
        return {
            "person": person,
            "response": response,
            "route": "finish",
            "audit_log": logs,
        }

    response = PersonResponse(
        results=[person.core_dict()],
        message=f"Found core record for {person.name}.",
        debug=_debug_for_query(query, outcome="found"),
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

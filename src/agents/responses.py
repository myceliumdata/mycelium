"""PersonResponse builders for supervisor routing outcomes."""

from __future__ import annotations

from models.state import MINIMUM_VIABLE_FIELDS, Person, PersonQuery, PersonResponse


def debug_for_query(query: PersonQuery, **extra: str) -> str:
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


def response_found(query: PersonQuery, person: Person) -> PersonResponse:
    return PersonResponse(
        results=[person.core_dict()],
        message=f"Found core record for {person.name}.",
        debug=debug_for_query(query, outcome="found"),
    )


def response_not_found(query: PersonQuery) -> PersonResponse:
    required = ", ".join(MINIMUM_VIABLE_FIELDS)
    return PersonResponse(
        results=[],
        message=_ingest_guidance_message(query.person_key),
        debug=debug_for_query(
            query,
            outcome="ingest_required",
            required_fields=required,
        ),
    )


def response_non_core(query: PersonQuery, person: Person, attributes: list[str]) -> PersonResponse:
    attr_list = ", ".join(attributes)
    return PersonResponse(
        results=[person.core_dict()],
        message=(
            f"We have a core record for {person.name}, but we're still researching "
            f"{attr_list}."
        ),
        debug=debug_for_query(
            query,
            outcome="non_core_requested",
            non_core_requested=attr_list,
        ),
    )


def response_ingest_success(query: PersonQuery, person: Person) -> PersonResponse:
    return PersonResponse(
        results=[person.core_dict()],
        message=f"Added core record for {person.name}.",
        debug=debug_for_query(query, outcome="ingested"),
    )


def response_ingest_failure(query: PersonQuery, error_summary: str) -> PersonResponse:
    return PersonResponse(
        results=[],
        message=f"Could not add core record: {error_summary}",
        debug=debug_for_query(query, outcome="ingest_failed", errors=error_summary),
    )

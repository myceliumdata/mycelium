"""PersonResponse builders for supervisor query outcomes."""

from __future__ import annotations

from typing import Any

from models.state import Person, PersonQuery, PersonResponse


def debug_for_query(query: PersonQuery, **extra: str) -> str:
    parts = [
        f"person_key={query.person_key!r}",
        f"requested_attributes={query.requested_attributes!r}",
    ]
    parts.extend(f"{key}={value!r}" for key, value in extra.items())
    return "; ".join(parts)


def _make_response(
    *,
    results: list[dict[str, Any]],
    message: str,
    debug: str,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> PersonResponse:
    return PersonResponse(
        results=results,
        message=message,
        debug=debug,
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_found(
    query: PersonQuery,
    person: Person,
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> PersonResponse:
    return _make_response(
        results=[person.core_dict()],
        message=f"Found core record for {person.name}.",
        debug=debug_for_query(query, outcome="found"),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_not_found(
    query: PersonQuery,
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> PersonResponse:
    return _make_response(
        results=[],
        message=(
            f"No core record found for {query.person_key!r}. "
            "This lookup did not match anyone in core storage."
        ),
        debug=debug_for_query(query, outcome="not_found"),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_non_core(
    query: PersonQuery,
    person: Person,
    attributes: list[str],
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> PersonResponse:
    attr_list = ", ".join(attributes)
    return _make_response(
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
        trace_id=trace_id,
        thread_id=thread_id,
    )

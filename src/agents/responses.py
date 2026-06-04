"""PersonResponse builders for supervisor query outcomes.

Unified in seed-data-context redesign. No more special 'core' layer.
results come from seed + specialist overrides (specialist wins).
See 3 scenarios in specialists.
"""

from __future__ import annotations

from typing import Any

from models.state import Person, PersonQuery, PersonResponse


def _debug_extra_value(value: Any) -> str:
    """Format debug key=value segments (lists/dicts and strings use repr)."""
    return repr(value)


def debug_for_query(query: PersonQuery, **extra: Any) -> str:
    parts = [
        f"person_key={query.person_key!r}",
        f"requested_attributes={query.requested_attributes!r}",
    ]
    parts.extend(
        f"{key}={_debug_extra_value(value)}" for key, value in extra.items()
    )
    return "; ".join(parts)


def _build_identity_results(
    persons: list[Person] | None = None,
    *,
    base_records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if base_records is not None:
        return list(base_records)
    if persons:
        return [p.core_dict() for p in persons]
    return []


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
    persons: list[Person] | None = None,
    *,
    base_records: list[dict[str, Any]] | None = None,
    classifications: list[dict[str, Any]] | None = None,
    specialist: str | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> PersonResponse:
    records = _build_identity_results(persons, base_records=base_records)
    n = len(records)
    if n == 1:
        name = records[0].get("name") or query.person_key
        message = f"Found record for {name}."
    else:
        message = f"Found {n} records for {query.person_key!r}."
    return _make_response(
        results=records,
        message=message,
        debug=debug_for_query(
            query,
            outcome="found",
            num_matches=str(n),
            **({"classifications": classifications} if classifications else {}),
            **({"specialist": specialist} if specialist else {}),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_not_found(
    query: PersonQuery,
    *,
    classifications: list[dict[str, Any]] | None = None,
    specialist: str | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> PersonResponse:
    return _make_response(
        results=[],
        message=(
            f"No record found for {query.person_key!r}. "
            "This lookup did not match anyone."
        ),
        debug=debug_for_query(
            query,
            outcome="not_found",
            **({"classifications": classifications} if classifications else {}),
            **({"specialist": specialist} if specialist else {}),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_non_core(
    query: PersonQuery,
    persons: list[Person] | None = None,
    attributes: list[str] | None = None,
    *,
    base_records: list[dict[str, Any]] | None = None,
    classifications: list[dict[str, Any]] | None = None,
    specialist: str | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> PersonResponse:
    attrs = attributes or []
    attr_list = ", ".join(attrs)
    records = _build_identity_results(persons, base_records=base_records)
    n = len(records)
    via_suffix = (
        f" (via {specialist})"
        if specialist and specialist != "core_data"
        else ""
    )
    if n == 1:
        name = records[0].get("name") or query.person_key
        message = (
            f"Found record for {name}. We're still researching "
            f"{attr_list}{via_suffix}."
        )
    else:
        message = (
            f"Found {n} records for {query.person_key!r}. We're still researching "
            f"{attr_list}{via_suffix}."
        )
    return _make_response(
        results=records,
        message=message,
        debug=debug_for_query(
            query,
            outcome="non_core_requested",
            non_core_requested=attr_list,
            num_matches=str(n),
            **({"classifications": classifications} if classifications else {}),
            **({"specialist": specialist} if specialist else {}),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )

"""QueryResponse builders for supervisor query outcomes.

Unified in seed-data-context redesign. No more special 'core' layer.
results come from seed + specialist overrides (specialist wins).
See 3 scenarios in specialists.
"""

from __future__ import annotations

from typing import Any

from models.state import (
    EntityQuery,
    QueryResponse,
    SeedRecord,
    normalized_requested_attributes,
)

_IDENTITY_SUMMARY_KEYS = ("id", "name", "employer")


def _debug_extra_value(value: Any) -> str:
    """Format debug key=value segments (lists/dicts and strings use repr)."""
    return repr(value)


def debug_for_query(query: EntityQuery, **extra: Any) -> str:
    parts = [
        f"entity_key={query.entity_key!r}",
        f"requested_attributes={query.requested_attributes!r}",
    ]
    parts.extend(
        f"{key}={_debug_extra_value(value)}" for key, value in extra.items()
    )
    return "; ".join(parts)


def _specialist_value_for_attr(
    contributions: list[dict[str, Any]],
    attr: str,
) -> tuple[Any | None, bool]:
    """Return (value, specialist_pending) from contributions for one attribute."""
    pending = False
    for contrib in contributions:
        sc = contrib.get("specialist_contrib") or {}
        values = sc.get("values") or {}
        if attr not in values:
            continue
        raw = values[attr]
        if raw == "pending":
            pending = True
        elif raw is not None:
            return raw, pending
    return None, pending


def merge_requested_record(
    seed_rec: dict[str, Any],
    contributions: list[dict[str, Any]],
    requested: list[str],
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Merge seed + specialist values for one record.

    Returns (merged record, provisional attribute names, unavailable names).
    Specialist non-pending values override seed; seed fills gaps while specialist is pending.
    """
    merged: dict[str, Any] = {"id": seed_rec.get("id", "")}
    provisional: list[str] = []
    unavailable: list[str] = []

    for attr in requested:
        spec_value, spec_pending = _specialist_value_for_attr(contributions, attr)
        if spec_value is not None:
            merged[attr] = spec_value
        elif attr in seed_rec and seed_rec.get(attr) not in (None, ""):
            merged[attr] = seed_rec[attr]
            if spec_pending:
                provisional.append(attr)
        elif spec_pending:
            unavailable.append(attr)
        else:
            unavailable.append(attr)

    return merged, provisional, unavailable


def shape_results(
    records: list[dict[str, Any]],
    requested: list[str] | None,
) -> list[dict[str, Any]]:
    """Filter result dicts to identity summary or requested attributes (+ id)."""
    normalized = normalized_requested_attributes(requested or [])
    if not normalized:
        shaped: list[dict[str, Any]] = []
        for rec in records:
            out = {k: rec[k] for k in _IDENTITY_SUMMARY_KEYS if k in rec}
            if out.get("id"):
                shaped.append(out)
        return shaped

    shaped = []
    for rec in records:
        out: dict[str, Any] = {"id": rec.get("id", "")}
        for attr in normalized:
            if attr in rec:
                out[attr] = rec[attr]
        shaped.append(out)
    return shaped


def message_for_assembled(
    query: EntityQuery,
    records: list[dict[str, Any]],
    *,
    provisional: list[str],
    unavailable: list[str],
    specialist_label: str | None = None,
) -> str:
    """Build user-facing message for assemble_response outcomes."""
    if not records:
        return (
            f"No record found for {query.entity_key!r}. "
            "This lookup did not match any record."
        )

    if len(records) == 1:
        name = records[0].get("name") or query.entity_key
        prefix = f"Found record for {name}"
    else:
        prefix = f"Found {len(records)} records for {query.entity_key!r}"

    parts: list[str] = [prefix]
    via = f" (via {specialist_label})" if specialist_label else ""

    if provisional:
        attrs = ", ".join(provisional)
        parts.append(
            f"{attrs} shown from seed; specialist verification in progress{via}.",
        )
    if unavailable:
        attrs = ", ".join(unavailable)
        parts.append(
            f"{attrs} not currently available but may be in the future{via}.",
        )

    if len(parts) == 1:
        parts[0] += "."
    else:
        parts[0] += "."

    return " ".join(parts)


def _build_identity_results(
    seed_records: list[SeedRecord] | None = None,
    *,
    base_records: list[dict[str, Any]] | None = None,
    requested: list[str] | None = None,
) -> list[dict[str, Any]]:
    if base_records is not None:
        records = list(base_records)
    elif seed_records:
        records = [record.core_dict() for record in seed_records]
    else:
        records = []
    return shape_results(records, requested)


def _make_response(
    *,
    results: list[dict[str, Any]],
    message: str,
    debug: str,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    return QueryResponse(
        results=results,
        message=message,
        debug=debug,
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_found(
    query: EntityQuery,
    seed_records: list[SeedRecord] | None = None,
    *,
    base_records: list[dict[str, Any]] | None = None,
    classifications: list[dict[str, Any]] | None = None,
    specialist: str | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    records = _build_identity_results(
        seed_records,
        base_records=base_records,
        requested=query.requested_attributes,
    )
    n = len(records)
    if n == 1:
        name = records[0].get("name") or query.entity_key
        message = f"Found record for {name}."
    else:
        message = f"Found {n} records for {query.entity_key!r}."
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
    query: EntityQuery,
    *,
    classifications: list[dict[str, Any]] | None = None,
    specialist: str | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    return _make_response(
        results=[],
        message=(
            f"No record found for {query.entity_key!r}. "
            "This lookup did not match any record."
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
    query: EntityQuery,
    seed_records: list[SeedRecord] | None = None,
    attributes: list[str] | None = None,
    *,
    base_records: list[dict[str, Any]] | None = None,
    classifications: list[dict[str, Any]] | None = None,
    specialist: str | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    attrs = attributes or []
    attr_list = ", ".join(attrs)
    records = _build_identity_results(
        seed_records,
        base_records=base_records,
        requested=attrs or query.requested_attributes,
    )
    n = len(records)
    via_suffix = (
        f" (via {specialist})"
        if specialist and specialist != "core_data"
        else ""
    )
    if n == 1:
        name = records[0].get("name") or query.entity_key
        message = (
            f"Found record for {name}. We're still researching "
            f"{attr_list}{via_suffix}."
        )
    else:
        message = (
            f"Found {n} records for {query.entity_key!r}. We're still researching "
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


def response_assembled(
    query: EntityQuery,
    *,
    merged_records: list[dict[str, Any]],
    provisional: list[str],
    unavailable: list[str],
    classifications: list[dict[str, Any]] | None = None,
    specialist_label: str | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
    debug_extra: dict[str, Any] | None = None,
) -> QueryResponse:
    """Final response after specialist contributions merged in assemble_response."""
    requested = normalized_requested_attributes(query.requested_attributes)
    records = shape_results(merged_records, requested)
    message = message_for_assembled(
        query,
        records,
        provisional=provisional,
        unavailable=unavailable,
        specialist_label=specialist_label,
    )
    extra = debug_extra or {}
    return _make_response(
        results=records,
        message=message,
        debug=debug_for_query(query, outcome="assembled", **extra),
        trace_id=trace_id,
        thread_id=thread_id,
    )

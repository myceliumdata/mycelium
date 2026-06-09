"""QueryResponse builders for supervisor query outcomes.

Unified in seed-data-context redesign. No more special 'core' layer.
results come from seed + specialist overrides (specialist wins).
See 3 scenarios in specialists.
"""

from __future__ import annotations

from typing import Any

from models.state import (
    EntityKeySuggestion,
    EntityQuery,
    QueryResponse,
    SeedRecord,
    normalized_requested_attributes,
)
from network.mvr import MvrPolicy, load_mvr

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


def _contrib_status_for_attr(
    contributions: list[dict[str, Any]],
    attr: str,
) -> str | None:
    """Return ``pending``, ``na``, ``found``, or ``None`` from specialist contributions."""
    for contrib in contributions:
        sc = contrib.get("specialist_contrib") or {}
        values = sc.get("values") or {}
        if attr not in values:
            continue
        raw = values[attr]
        if raw == "pending":
            return "pending"
        if raw == "N/A":
            return "na"
        return "found"
    return None


def _new_specialist_categories(audit_log: list[str] | None) -> set[str]:
    """Categories whose specialists were created during this query turn."""
    created: set[str] = set()
    marker = "Supervisor: created new specialist "
    for line in audit_log or []:
        if marker not in line or " for category " not in line:
            continue
        part = line.split(" for category ", 1)[1]
        created.add(part.rstrip("."))
    return created


def _classifications_for_attrs(
    attrs: list[str],
    classifications: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if classifications:
        return classifications
    from agents.classification import get_category_tree

    tree = get_category_tree()
    return [tree.classify(attr).model_dump() for attr in attrs]


def partition_attribute_buckets(
    requested: list[str],
    classifications: list[dict[str, Any]],
    shaped_records: list[dict[str, Any]],
    contributions: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Partition requested attributes into found / researching / unavailable / out_of_scope."""
    buckets: dict[str, list[str]] = {
        "found": [],
        "researching": [],
        "unavailable": [],
        "out_of_scope": [],
    }
    clf_by_attr = {
        cl["attribute"]: cl for cl in classifications if cl.get("attribute")
    }

    for attr in requested:
        category = (clf_by_attr.get(attr) or {}).get("category") or "unknown"
        if category == "unknown":
            buckets["out_of_scope"].append(attr)
            continue

        status = _contrib_status_for_attr(contributions, attr)
        if status == "na":
            buckets["unavailable"].append(attr)
        elif status == "pending":
            buckets["researching"].append(attr)
        elif status == "found":
            buckets["found"].append(attr)
        else:
            has_value = any(
                attr in rec
                and rec.get(attr) not in (None, "", "N/A", "pending")
                for rec in shaped_records
            )
            if has_value:
                buckets["found"].append(attr)
            else:
                buckets["researching"].append(attr)

    return buckets


def build_query_message(
    query: EntityQuery,
    *,
    records: list[dict[str, Any]],
    classifications: list[dict[str, Any]],
    contributions: list[dict[str, Any]],
    audit_log: list[str] | None = None,
) -> tuple[str, dict[str, list[str]]]:
    """Build classification-aware QueryResponse.message and attribute buckets."""
    requested = normalized_requested_attributes(query.requested_attributes)

    if not records:
        return f"No record found for {query.entity_key!r}.", {
            "found": [],
            "researching": [],
            "unavailable": [],
            "out_of_scope": [],
        }

    if len(records) == 1:
        name = records[0].get("name") or query.entity_key
        parts: list[str] = [f"Found record for {name}."]
    else:
        parts = [f"Found {len(records)} records for {query.entity_key!r}."]

    if not requested:
        return parts[0], {
            "found": [],
            "researching": [],
            "unavailable": [],
            "out_of_scope": [],
        }

    buckets = partition_attribute_buckets(
        requested,
        classifications,
        records,
        contributions,
    )
    clf_by_attr = {
        cl["attribute"]: cl for cl in classifications if cl.get("attribute")
    }
    new_cats = _new_specialist_categories(audit_log)

    for attr in buckets["researching"]:
        category = (clf_by_attr.get(attr) or {}).get("category") or "unknown"
        if category in new_cats:
            parts.append(
                f"Classified {attr} as {category} — setting up a {category} "
                f"specialist to research it.",
            )
        else:
            parts.append(f"Classified {attr} as {category} — researching.")

    for attr in buckets["unavailable"]:
        category = (clf_by_attr.get(attr) or {}).get("category") or "unknown"
        parts.append(
            f"Classified {attr} as {category} — {attr} not found for this record.",
        )

    for attr in buckets["out_of_scope"]:
        parts.append(
            f"{attr} could not be classified into this network's ontology — "
            "it does not appear related to this network.",
        )

    return " ".join(parts), buckets


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
    outcome: str | None = None,
    suggestions: list[EntityKeySuggestion] | None = None,
    required_fields: list[str] | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    return QueryResponse(
        results=results,
        message=message,
        debug=debug,
        outcome=outcome,
        suggestions=suggestions or [],
        required_fields=required_fields or [],
        trace_id=trace_id,
        thread_id=thread_id,
    )


def _required_field_hint(field: str) -> str:
    hints = {
        "employer": "employer (who they work for)",
    }
    return hints.get(field, field)


def _required_fields_phrase(required_fields: list[str]) -> str:
    if not required_fields:
        return "required bind fields"
    return ", ".join(_required_field_hint(field) for field in required_fields)


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
        outcome="found",
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
    message, _buckets = build_query_message(
        query,
        records=[],
        classifications=classifications or [],
        contributions=[],
    )
    return _make_response(
        results=[],
        message=message,
        outcome="not_found",
        debug=debug_for_query(
            query,
            outcome="not_found",
            **({"classifications": classifications} if classifications else {}),
            **({"specialist": specialist} if specialist else {}),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_entity_unresolved(
    query: EntityQuery,
    suggestions: list[EntityKeySuggestion],
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Near-miss entity_key: suggest retries without returning attribute data."""
    if not suggestions:
        return response_not_found(query, trace_id=trace_id, thread_id=thread_id)

    top = suggestions[0]
    employer_hint = f" ({top.employer})" if top.employer else ""
    if len(suggestions) == 1:
        message = (
            f"No exact match for {query.entity_key!r}. "
            f"Did you mean {top.entity_key!r}{employer_hint}? "
            "Re-query with that entity_key to continue."
        )
    else:
        names = ", ".join(f"{item.entity_key!r}" for item in suggestions[:3])
        message = (
            f"No exact match for {query.entity_key!r}. "
            f"Did you mean one of: {names}? "
            "Re-query with a suggested entity_key to continue."
        )

    return _make_response(
        results=[],
        message=message,
        outcome="entity_key_unresolved",
        suggestions=suggestions,
        debug=debug_for_query(
            query,
            outcome="entity_key_unresolved",
            suggestions=[item.model_dump() for item in suggestions],
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_entity_unknown(
    query: EntityQuery,
    *,
    mvr: MvrPolicy | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Unknown entity: no seed match and no near-miss suggestions; return MVR gaps."""
    policy = mvr or load_mvr()
    required_fields = policy.required_fields_for_entity_key(query.entity_key)
    fields_phrase = _required_fields_phrase(required_fields)
    if query.requested_attributes:
        attrs = ", ".join(query.requested_attributes)
        message = (
            f"No record for {query.entity_key!r}. "
            f"To research {attrs}, provide {fields_phrase}. "
            "Re-query with the same entity_key when you have it."
        )
    else:
        message = (
            f"No record for {query.entity_key!r}. "
            f"Provide {fields_phrase} to bind this entity."
        )

    return _make_response(
        results=[],
        message=message,
        outcome="entity_unknown",
        required_fields=required_fields,
        debug=debug_for_query(
            query,
            outcome="entity_unknown",
            required_fields=required_fields,
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
    attrs = normalized_requested_attributes(attributes or query.requested_attributes)
    records = _build_identity_results(
        seed_records,
        base_records=base_records,
        requested=attrs or query.requested_attributes,
    )
    clfs = _classifications_for_attrs(attrs, classifications)
    shaped = shape_results(records, attrs)
    message, buckets = build_query_message(
        query,
        records=shaped,
        classifications=clfs,
        contributions=[],
    )
    n = len(records)
    return _make_response(
        results=shaped,
        message=message,
        outcome="assembled",
        debug=debug_for_query(
            query,
            outcome="assembled",
            num_matches=str(n),
            **buckets,
            **({"classifications": clfs} if clfs else {}),
            **({"specialist": specialist} if specialist else {}),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_assembled(
    query: EntityQuery,
    *,
    merged_records: list[dict[str, Any]],
    classifications: list[dict[str, Any]] | None = None,
    contributions: list[dict[str, Any]] | None = None,
    audit_log: list[str] | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
    debug_extra: dict[str, Any] | None = None,
) -> QueryResponse:
    """Final response after specialist contributions merged in assemble_response."""
    requested = normalized_requested_attributes(query.requested_attributes)
    records = shape_results(merged_records, requested)
    clfs = classifications or []
    contribs = contributions or []
    message, buckets = build_query_message(
        query,
        records=records,
        classifications=clfs,
        contributions=contribs,
        audit_log=audit_log,
    )
    extra = {**(debug_extra or {}), **buckets}
    if clfs:
        extra.setdefault("classifications", clfs)
    return _make_response(
        results=records,
        message=message,
        outcome="assembled",
        debug=debug_for_query(query, outcome="assembled", **extra),
        trace_id=trace_id,
        thread_id=thread_id,
    )

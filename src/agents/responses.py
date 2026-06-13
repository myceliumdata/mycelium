"""QueryResponse builders for supervisor query outcomes.

Unified in seed-data-context redesign. No more special 'core' layer.
results come from seed + specialist overrides (specialist wins).
See 3 scenarios in specialists.
"""

from __future__ import annotations

from typing import Any

from models.state import (
    DeliveryPayload,
    EntityKeySuggestion,
    EntityQuery,
    QueryResponse,
    IdentityRecord,
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
    identity_records: list[IdentityRecord] | None = None,
    *,
    base_records: list[dict[str, Any]] | None = None,
    requested: list[str] | None = None,
) -> list[dict[str, Any]]:
    if base_records is not None:
        records = list(base_records)
    elif identity_records:
        records = [record.core_dict() for record in identity_records]
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
    quote: dict[str, Any] | None = None,
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
        quote=quote,
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
    identity_records: list[IdentityRecord] | None = None,
    *,
    base_records: list[dict[str, Any]] | None = None,
    classifications: list[dict[str, Any]] | None = None,
    specialist: str | None = None,
    message: str | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    records = _build_identity_results(
        identity_records,
        base_records=base_records,
        requested=query.requested_attributes,
    )
    n = len(records)
    if message is None:
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
    message: str | None = None,
) -> QueryResponse:
    if message is None:
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


def response_lookup_resolved(
    query: EntityQuery,
    *,
    total_matches: int,
    delivery: DeliveryPayload,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    if (query.id or "").strip():
        message = f"Resolved {total_matches} match(es) for id."
    else:
        message = f"Resolved {total_matches} matches for lookup."
    return QueryResponse(
        outcome="lookup_resolved",
        total_matches=total_matches,
        delivery=delivery,
        results=[],
        message=message,
        debug=debug_for_query(
            query,
            outcome="lookup_resolved",
            total_matches=total_matches,
            delivery_id=delivery.delivery_id,
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
    """Unknown entity: no registry match and no near-miss suggestions; return MVR gaps."""
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


def response_entity_under_specified(
    query: EntityQuery,
    required_fields: list[str],
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Partial binding: MVR fields still missing after binding attempt."""
    fields_phrase = _required_fields_phrase(required_fields)
    if query.requested_attributes:
        attrs = ", ".join(query.requested_attributes)
        message = (
            f"No record for {query.entity_key!r}. "
            f"To research {attrs}, complete binding with {fields_phrase}. "
            "Re-query with the same entity_key and binding when ready."
        )
    else:
        message = (
            f"No record for {query.entity_key!r}. "
            f"Complete binding with {fields_phrase}."
        )

    return _make_response(
        results=[],
        message=message,
        outcome="entity_under_specified",
        required_fields=required_fields,
        debug=debug_for_query(
            query,
            outcome="entity_under_specified",
            required_fields=required_fields,
            binding=query.binding,
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_entity_bound_provisional(
    query: EntityQuery,
    record: dict[str, Any],
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """New provisional registry bind; identity only — no attribute research."""
    name = record.get("name") or query.entity_key
    employer = record.get("employer")
    employer_phrase = f" at {employer}" if employer else ""
    message = (
        f"Bound provisional record for {name}{employer_phrase}. "
        "Core validation and attribute research are not available until a later step."
    )
    results = [
        {
            "id": record.get("id", ""),
            "name": name,
            "employer": employer,
        },
    ]
    return _make_response(
        results=results,
        message=message,
        outcome="entity_bound_provisional",
        required_fields=[],
        debug=debug_for_query(
            query,
            outcome="entity_bound_provisional",
            registry_id=record.get("id"),
            binding=query.binding,
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_entity_validated(
    query: EntityQuery,
    record: dict[str, Any],
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """MVR validation passed; registry entity promoted to validated."""
    name = record.get("name") or query.entity_key
    employer = record.get("employer")
    results = [
        {
            "id": record.get("id", ""),
            "name": name,
            "employer": employer,
        },
    ]
    return _make_response(
        results=results,
        message="Core record validated.",
        outcome="entity_validated",
        required_fields=[],
        debug=debug_for_query(
            query,
            outcome="entity_validated",
            registry_id=record.get("id"),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_quote_required(
    query: EntityQuery,
    quote: dict[str, Any],
    *,
    base_records: list[dict[str, Any]] | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Metering gate blocked progress until quote is accepted."""
    results = list(base_records or [])
    total = quote.get("total_usd")
    cache_state = quote.get("cache_state", "miss")
    message = (
        f"Quote required before research or delivery (cache_state={cache_state}, "
        f"total_usd={total}). Retry with quote_id after acceptance."
    )
    return _make_response(
        results=results,
        message=message,
        outcome="quote_required",
        quote=quote,
        debug=debug_for_query(
            query,
            outcome="quote_required",
            quote_id=quote.get("quote_id"),
            cache_state=cache_state,
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_payment_required(
    query: EntityQuery,
    quote: dict[str, Any],
    *,
    base_records: list[dict[str, Any]] | None = None,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Metering gate blocked: quote must be paid before quote_id unlocks work."""
    results = list(base_records or [])
    total = quote.get("total_usd")
    quote_id = quote.get("quote_id")
    message = (
        f"Payment required before work runs (quote_id={quote_id}, total_usd={total}). "
        "Call pay_quote with this quote_id, then retry query_entity with the same quote_id."
    )
    return _make_response(
        results=results,
        message=message,
        outcome="payment_required",
        quote=quote,
        debug=debug_for_query(
            query,
            outcome="payment_required",
            quote_id=quote_id,
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_principal_required(
    query: EntityQuery,
    *,
    funding_model: str,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Metering blocked: billing principal required for the network funding model."""
    message = (
        f"Billing principal required for funding model {funding_model!r}. "
        "Supply principal on EntityQuery (kind + id) and retry."
    )
    return _make_response(
        results=[],
        message=message,
        outcome="principal_required",
        required_fields=[],
        debug=debug_for_query(
            query,
            outcome="principal_required",
            funding_model=funding_model,
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_validation_failed(
    query: EntityQuery,
    record: dict[str, Any],
    *,
    summary: str,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Validation failed; entity stays provisional (outcome found per Q5b)."""
    name = record.get("name") or query.entity_key
    employer = record.get("employer")
    employer_phrase = f" at {employer}" if employer else ""
    message = (
        f"Found provisional record for {name}{employer_phrase}. "
        f"Core validation failed: {summary}"
    )
    results = [
        {
            "id": record.get("id", ""),
            "name": name,
            "employer": employer,
        },
    ]
    return _make_response(
        results=results,
        message=message,
        outcome="found",
        required_fields=[],
        debug=debug_for_query(
            query,
            outcome="found",
            validation_failed=True,
            validation_summary=summary,
            registry_id=record.get("id"),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_research_gated(
    query: EntityQuery,
    record: dict[str, Any],
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Provisional registry entity with attrs requested: identity only, gate message."""
    from agents.research_gate import RESEARCH_GATE_MESSAGE

    name = record.get("name") or query.entity_key
    employer = record.get("employer")
    employer_phrase = f" at {employer}" if employer else ""
    message = (
        f"Found provisional record for {name}{employer_phrase}. "
        f"{RESEARCH_GATE_MESSAGE}"
    )
    results = [
        {
            "id": record.get("id", ""),
            "name": name,
            "employer": employer,
        },
    ]
    return _make_response(
        results=results,
        message=message,
        outcome="found",
        required_fields=[],
        debug=debug_for_query(
            query,
            outcome="found",
            research_gated=True,
            registry_id=record.get("id"),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_non_core(
    query: EntityQuery,
    identity_records: list[IdentityRecord] | None = None,
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
        identity_records,
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

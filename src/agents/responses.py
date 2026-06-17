"""QueryResponse builders for supervisor query outcomes.

Unified in seed-data-context redesign. No more special 'core' layer.
results come from seed + specialist overrides (specialist wins).
See 3 scenarios in specialists.
"""

from __future__ import annotations

from typing import Any

from models.state import (
    DeliveryPayload,
    LookupSuggestion,
    EntityQuery,
    QueryResponse,
    IdentityRecord,
    normalized_requested_attributes,
)

def _identity_summary_keys() -> tuple[str, ...]:
    from network.mvr import load_mvr

    keys: list[str] = ["id"]
    for field in load_mvr().bind_fields:
        key = field.strip().lower()
        if key:
            keys.append(key)
    return tuple(keys)


def _mvr_bind_field_names() -> list[str]:
    from network.mvr import load_mvr

    return [
        field.strip().lower()
        for field in load_mvr().bind_fields
        if field.strip()
    ]


def _identity_records_from_match(matched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build identity rows for response shaping (id + active MVR bind fields)."""
    bind_fields = _mvr_bind_field_names()
    records: list[dict[str, Any]] = []
    for rec in matched:
        out: dict[str, Any] = {"id": rec.get("id", "")}
        for field in bind_fields:
            if field in rec:
                out[field] = rec[field]
        records.append(out)
    return records


def _identity_message_label(
    record: dict[str, Any],
    *,
    query: EntityQuery | None = None,
) -> str:
    """Human-readable identity label from MVR bind fields (e.g. 'Ada at Acme')."""
    bind_fields = _mvr_bind_field_names()
    if not bind_fields:
        if query is not None:
            return _query_target_label(query)
        return str(record.get("id") or "record")

    primary = bind_fields[0]
    primary_value = record.get(primary)
    if primary_value is None or not str(primary_value).strip():
        if query is not None:
            return _query_target_label(query)
        return str(record.get("id") or "record")

    label = str(primary_value).strip()
    for field in bind_fields[1:]:
        value = record.get(field)
        if value is not None and str(value).strip():
            label = f"{label} at {str(value).strip()}"
    return label


def _debug_extra_value(value: Any) -> str:
    """Format debug key=value segments (lists/dicts and strings use repr)."""
    return repr(value)


def _query_target_label(query: EntityQuery) -> str:
    entity_id = (query.id or "").strip()
    if entity_id:
        return entity_id
    if query.lookup:
        return str(query.lookup)
    delivery_id = (query.delivery_id or "").strip()
    if delivery_id:
        return delivery_id
    return "query"


def debug_for_query(query: EntityQuery, **extra: Any) -> str:
    parts = [
        f"id={(query.id or '').strip()!r}",
        f"lookup={query.lookup!r}",
        f"delivery_id={(query.delivery_id or '').strip()!r}",
        f"requested_attributes={query.requested_attributes!r}",
    ]
    parts.extend(
        f"{key}={_debug_extra_value(value)}" for key, value in extra.items()
    )
    return "; ".join(parts)


def _specialist_value_for_attr(
    contributions: list[dict[str, Any]],
    attr: str,
    *,
    entity_id: str | None = None,
) -> tuple[Any | None, bool]:
    """Return (value, specialist_pending) from contributions for one attribute."""
    pending = False
    for contrib in contributions:
        sc = contrib.get("specialist_contrib") or {}
        if entity_id:
            contrib_entity = sc.get("id") or contrib.get("entity_id")
            if contrib_entity and str(contrib_entity) != entity_id:
                continue
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
    entity_id = str(seed_rec.get("id") or "") or None

    for attr in requested:
        spec_value, spec_pending = _specialist_value_for_attr(
            contributions,
            attr,
            entity_id=entity_id,
        )
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
            out = {k: rec[k] for k in _identity_summary_keys() if k in rec}
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
    *,
    entity_id: str | None = None,
) -> str | None:
    """Return ``pending``, ``na``, ``found``, or ``None`` from specialist contributions."""
    for contrib in contributions:
        sc = contrib.get("specialist_contrib") or {}
        if entity_id:
            contrib_entity = sc.get("id") or contrib.get("entity_id")
            if contrib_entity and str(contrib_entity) != entity_id:
                continue
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

        if len(shaped_records) > 1:
            statuses: list[str | None] = []
            for rec in shaped_records:
                entity_id = str(rec.get("id") or "") or None
                statuses.append(
                    _contrib_status_for_attr(
                        contributions,
                        attr,
                        entity_id=entity_id,
                    ),
                )
            if any(status == "pending" for status in statuses):
                buckets["researching"].append(attr)
            elif statuses and all(status == "na" for status in statuses):
                buckets["unavailable"].append(attr)
            elif statuses and all(status == "found" for status in statuses):
                buckets["found"].append(attr)
            elif any(
                rec.get(attr) not in (None, "", "N/A", "pending")
                for rec in shaped_records
            ):
                buckets["found"].append(attr)
            else:
                buckets["researching"].append(attr)
            continue

        entity_id = str(shaped_records[0].get("id") or "") or None
        status = _contrib_status_for_attr(
            contributions,
            attr,
            entity_id=entity_id,
        )
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
    requested_attributes: list[str] | None = None,
) -> tuple[str, dict[str, list[str]]]:
    """Build classification-aware QueryResponse.message and attribute buckets."""
    requested = normalized_requested_attributes(
        requested_attributes
        if requested_attributes is not None
        else query.requested_attributes
    )

    if not records:
        return f"No record found for {_query_target_label(query)!r}.", {
            "found": [],
            "researching": [],
            "unavailable": [],
            "out_of_scope": [],
        }

    if len(records) == 1:
        parts: list[str] = [
            f"Found record for {_identity_message_label(records[0], query=query)}.",
        ]
    else:
        parts = [f"Found {len(records)} records for {_query_target_label(query)!r}."]

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
    suggestions: list[LookupSuggestion] | None = None,
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
            message = f"Found record for {_identity_message_label(records[0], query=query)}."
        else:
            message = f"Found {n} records for {_query_target_label(query)!r}."
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
    if delivery.create_on_deliver:
        message = (
            "No registry match. Full MVR lookup — step 2 will create a "
            "provisional entity, then deliver."
        )
    elif (query.id or "").strip():
        match_word = "match" if total_matches == 1 else "matches"
        message = (
            f"{total_matches} registry {match_word} for id. "
            "Use delivery_id on step 2 to deliver."
        )
    elif total_matches == 1:
        message = "1 registry match. Use delivery_id on step 2 to deliver."
    else:
        message = (
            f"{total_matches} registry matches. Use delivery_id on step 2 to deliver."
        )
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


def response_lookup_incomplete(
    query: EntityQuery,
    *,
    required_fields: list[str],
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Step-1 partial lookup with 0 hits — missing MVR bind fields for create."""
    missing = ", ".join(required_fields) if required_fields else "MVR bind fields"
    message = (
        f"No registry match for lookup {query.lookup!r}. Partial lookup searches "
        f"the registry only. To create a new entity, include: {missing}."
    )
    return QueryResponse(
        outcome="lookup_incomplete",
        total_matches=0,
        required_fields=list(required_fields),
        results=[],
        message=message,
        debug=debug_for_query(
            query,
            outcome="lookup_incomplete",
            required_fields=required_fields,
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def _lookup_suggested_message(
    suggestions: list[LookupSuggestion],
) -> str:
    reasons = {item.reason for item in suggestions}
    if "same_bind_field_conflict" in reasons:
        return (
            "A registry row matches other bind fields but conflicts on one field. "
            "Retry with suggestions[].suggested_lookup or suggestions[].id. Set "
            "confirm_new_entity=true only if you intend a new bind."
        )
    if "bind_field_fuzzy_match" in reasons:
        return (
            "Near-miss registry bind field found. Retry with a corrected lookup map "
            "(suggestions[].suggested_lookup)."
        )
    return (
        "Near-miss registry names found. Retry with suggestions[].suggested_lookup "
        "or suggestions[].id."
    )


def response_lookup_suggested(
    query: EntityQuery,
    *,
    suggestions: list[LookupSuggestion],
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Step-1 full MVR with 0 hits — structured near-miss or same-name guidance."""
    return QueryResponse(
        outcome="lookup_suggested",
        total_matches=0,
        suggestions=list(suggestions),
        results=[],
        message=_lookup_suggested_message(suggestions),
        debug=debug_for_query(
            query,
            outcome="lookup_suggested",
            suggestion_count=len(suggestions),
        ),
        trace_id=trace_id,
        thread_id=thread_id,
    )


def response_quote_required(
    query: EntityQuery,
    quote: dict[str, Any],
    *,
    base_records: list[dict[str, Any]] | None = None,
    total_matches: int | None = None,
    delivery: DeliveryPayload | None = None,
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
    return QueryResponse(
        results=results,
        message=message,
        debug=debug_for_query(
            query,
            outcome="quote_required",
            quote_id=quote.get("quote_id"),
            cache_state=cache_state,
        ),
        outcome="quote_required",
        quote=quote,
        total_matches=total_matches,
        delivery=delivery,
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
    label = _identity_message_label(record, query=query)
    message = (
        f"Found provisional record for {label}. "
        f"Core validation failed: {summary}"
    )
    results = _identity_records_from_match([record])
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
    records: list[dict[str, Any]],
    *,
    trace_id: str | None = None,
    thread_id: str | None = None,
) -> QueryResponse:
    """Registry batch with attrs requested but gate blocks research: identity rows only."""
    from agents.research_gate import RESEARCH_GATE_MESSAGE

    matched = list(records)
    if not matched:
        return _make_response(
            results=[],
            message=RESEARCH_GATE_MESSAGE,
            outcome="found",
            required_fields=[],
            debug=debug_for_query(query, outcome="found", research_gated=True),
            trace_id=trace_id,
            thread_id=thread_id,
        )

    results = _identity_records_from_match(matched)

    provisional_count = sum(
        1 for rec in matched if rec.get("_validation_state") != "validated"
    )
    total = len(matched)

    if total == 1:
        rec = matched[0]
        label = _identity_message_label(rec, query=query)
        if rec.get("_validation_state") == "validated":
            message = (
                f"Found record for {label}. "
                f"{RESEARCH_GATE_MESSAGE}"
            )
        else:
            message = (
                f"Found provisional record for {label}. "
                f"{RESEARCH_GATE_MESSAGE}"
            )
    else:
        message = (
            f"Found {total} records. Attribute research blocked for "
            f"{provisional_count} provisional row(s). "
            f"{RESEARCH_GATE_MESSAGE}"
        )

    return _make_response(
        results=results,
        message=message,
        outcome="found",
        required_fields=[],
        debug=debug_for_query(
            query,
            outcome="found",
            research_gated=True,
            registry_id=matched[0].get("id"),
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
    requested_attributes: list[str] | None = None,
) -> QueryResponse:
    """Final response after specialist contributions merged in assemble_response."""
    requested = normalized_requested_attributes(
        requested_attributes
        if requested_attributes is not None
        else query.requested_attributes
    )
    records = shape_results(merged_records, requested)
    clfs = classifications or []
    contribs = contributions or []
    message, buckets = build_query_message(
        query,
        records=records,
        classifications=clfs,
        contributions=contribs,
        audit_log=audit_log,
        requested_attributes=requested,
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

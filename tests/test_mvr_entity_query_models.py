"""Smoke tests: MVR redesign EntityQuery / QueryResponse target protocol models (M3)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.state import (
    DeliveryPayload,
    EntityQuery,
    QueryResponse,
    entity_query_is_delivery_step,
)
from mycelium_mcp.server import _neutral_json_schema


@pytest.mark.smoke
def test_entity_query_step1_by_id() -> None:
    query = EntityQuery(id="3c3daf80-5e10-411e-8961-3e8d0f3421d4")
    assert not entity_query_is_delivery_step(query)
    assert query.entity_key == ""


@pytest.mark.smoke
def test_entity_query_step1_by_lookup() -> None:
    query = EntityQuery(
        lookup={"employer": "IBM"},
        requested_attributes=["linkedin"],
        provenance=True,
    )
    assert query.lookup == {"employer": "IBM"}
    assert query.requested_attributes == ["linkedin"]
    assert query.provenance is True


@pytest.mark.smoke
def test_entity_query_step1_legacy_entity_key() -> None:
    query = EntityQuery(entity_key="Nichanan Kesonpat", binding={"employer": "Acme"})
    assert query.entity_key == "Nichanan Kesonpat"
    assert query.binding == {"employer": "Acme"}


@pytest.mark.smoke
def test_entity_query_step2_delivery_only() -> None:
    query = EntityQuery(delivery_id="d_abc123", quote_id="q_xyz789")
    assert entity_query_is_delivery_step(query)
    assert query.entity_key == ""
    assert query.quote_id == "q_xyz789"


@pytest.mark.smoke
@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (
            {"delivery_id": "d_x", "entity_key": "Ada"},
            "step 2 accepts only delivery_id",
        ),
        (
            {"delivery_id": "d_x", "lookup": {"employer": "IBM"}},
            "step 2 accepts only delivery_id",
        ),
        (
            {"delivery_id": "d_x", "id": "uuid"},
            "step 2 accepts only delivery_id",
        ),
        (
            {"delivery_id": "d_x", "binding": {"employer": "IBM"}},
            "step 2 accepts only delivery_id",
        ),
        (
            {"delivery_id": "d_x", "requested_attributes": ["email"]},
            "requested_attributes are step 1 only",
        ),
        (
            {"delivery_id": "d_x", "provenance": True},
            "provenance is step 1 only",
        ),
        (
            {},
            "step 1 requires id, lookup, or entity_key",
        ),
        (
            {"lookup": {}},
            "step 1 requires id, lookup, or entity_key",
        ),
    ],
)
def test_entity_query_step_validation_rejects(payload: dict, match: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        EntityQuery.model_validate(payload)
    assert match in str(exc_info.value)


@pytest.mark.smoke
def test_query_response_lookup_resolved_serializes() -> None:
    response = QueryResponse(
        outcome="lookup_resolved",
        total_matches=237,
        delivery=DeliveryPayload(
            delivery_id="d_abc123",
            expires_at="2026-06-13T12:05:00Z",
        ),
        results=[],
        message="237 matches; use delivery_id to fetch results.",
        debug="outcome='lookup_resolved'; total_matches=237",
    )
    payload = response.public_dict()
    assert payload["outcome"] == "lookup_resolved"
    assert payload["total_matches"] == 237
    assert payload["delivery"] == {
        "delivery_id": "d_abc123",
        "expires_at": "2026-06-13T12:05:00Z",
    }
    assert "create_on_deliver" not in payload["delivery"]
    assert payload["results"] == []
    assert "quote" not in payload
    assert "provenance" not in payload


@pytest.mark.smoke
def test_public_dict_step2_found_omits_step1_fields() -> None:
    response = QueryResponse(
        outcome="found",
        total_matches=None,
        delivery=None,
        quote=None,
        provenance=None,
        results=[{"id": "u1", "name": "Ada"}],
        message="Found record for Ada.",
    )
    payload = response.public_dict()
    assert payload["outcome"] == "found"
    assert payload["results"] == [{"id": "u1", "name": "Ada"}]
    assert "total_matches" not in payload
    assert "delivery" not in payload
    assert "quote" not in payload
    assert "provenance" not in payload


@pytest.mark.smoke
def test_public_dict_step1_lookup_resolved_includes_matches() -> None:
    response = QueryResponse(
        outcome="lookup_resolved",
        total_matches=0,
        delivery=DeliveryPayload(
            delivery_id="d_abc123",
            expires_at="2026-06-13T12:05:00Z",
            create_on_deliver=True,
        ),
        quote=None,
        provenance=None,
        results=[],
        message="0 matches; step 2 will create.",
    )
    payload = response.public_dict()
    assert payload["total_matches"] == 0
    assert payload["delivery"]["delivery_id"] == "d_abc123"
    assert payload["delivery"]["create_on_deliver"] is True
    assert "quote" not in payload
    assert "provenance" not in payload


@pytest.mark.smoke
def test_public_dict_quote_required_includes_quote() -> None:
    response = QueryResponse(
        outcome="quote_required",
        total_matches=1,
        delivery=DeliveryPayload(
            delivery_id="d_quote",
            expires_at="2026-06-13T12:05:00Z",
        ),
        quote={"quote_id": "q_1", "total_usd": 1.0},
        results=[],
        message="Quote required.",
    )
    payload = response.public_dict()
    assert payload["total_matches"] == 1
    assert payload["delivery"]["delivery_id"] == "d_quote"
    assert payload["quote"] == {"quote_id": "q_1", "total_usd": 1.0}
    assert "provenance" not in payload


@pytest.mark.smoke
def test_public_dict_omits_empty_negotiation_fields() -> None:
    response = QueryResponse(
        outcome="found",
        results=[{"id": "u1", "name": "Ada"}],
        message="Found record for Ada.",
    )
    payload = response.public_dict()
    assert "required_fields" not in payload
    assert "suggestions" not in payload


@pytest.mark.smoke
def test_public_dict_includes_required_fields_when_incomplete() -> None:
    response = QueryResponse(
        outcome="lookup_incomplete",
        total_matches=0,
        required_fields=["employer"],
        results=[],
        message="Missing employer.",
    )
    payload = response.public_dict()
    assert payload["required_fields"] == ["employer"]
    assert "delivery" not in payload


@pytest.mark.smoke
def test_mcp_entity_query_schema_includes_target_fields() -> None:
    schema = _neutral_json_schema(EntityQuery)
    props = schema.get("properties") or {}
    for field in ("id", "lookup", "delivery_id", "entity_key", "binding"):
        assert field in props
    assert "Deprecated" in (props["entity_key"].get("description") or "")
    assert "Deprecated" in (props["binding"].get("description") or "")
    description = schema.get("description") or ""
    assert "delivery_id" in description
    assert "lookup" in description


@pytest.mark.smoke
def test_mcp_query_response_schema_includes_lookup_resolved_fields() -> None:
    schema = _neutral_json_schema(QueryResponse)
    props = schema.get("properties") or {}
    assert "total_matches" in props
    assert "delivery" in props
    description = schema.get("description") or ""
    assert "lookup_resolved" in description
    assert "total_matches" in description

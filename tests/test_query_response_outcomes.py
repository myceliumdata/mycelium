"""Smoke tests: QueryResponse outcome consistency across builders and MCP schema."""

from __future__ import annotations

import json

import pytest

from agents.responses import (
    response_assembled,
    response_found,
    response_lookup_incomplete,
    response_lookup_suggested,
    response_non_core,
    response_not_found,
)
from models.state import EntityQuery, IdentityRecord, LookupSuggestion, QueryResponse
from mycelium_mcp.server import _neutral_json_schema


def _assert_outcome(response: QueryResponse, expected: str) -> None:
    assert response.outcome == expected
    assert f"outcome={expected!r}" in response.debug


@pytest.mark.smoke
@pytest.mark.parametrize(
    ("builder", "kwargs", "expected_outcome"),
    [
        (
            response_found,
            {
                "query": EntityQuery(lookup={"name": "Ada", "employer": "Lab"}),
                "identity_records": [
                    IdentityRecord(id="p1", bind_values={"name": "Ada", "employer": "Lab"}),
                ],
            },
            "found",
        ),
        (
            response_not_found,
            {"query": EntityQuery(lookup={"name": "Missing"})},
            "not_found",
        ),
        (
            response_lookup_suggested,
            {
                "query": EntityQuery(lookup={"name": "Andrea Kalman"}),
                "suggestions": [
                    LookupSuggestion(
                        suggested_lookup={"name": "Andrea Kalmans"},
                        id="s1",
                        name="Andrea Kalmans",
                        employer="Lontra Ventures",
                        score=0.92,
                    ),
                ],
            },
            "lookup_suggested",
        ),
        (
            response_non_core,
            {
                "query": EntityQuery(
                    lookup={"name": "Ada", "employer": "Lab"},
                    requested_attributes=["email"],
                ),
                "identity_records": [
                    IdentityRecord(id="p1", bind_values={"name": "Ada", "employer": "Lab"}),
                ],
                "attributes": ["email"],
            },
            "assembled",
        ),
        (
            response_assembled,
            {
                "query": EntityQuery(
                    lookup={"name": "Ada", "employer": "Lab"},
                    requested_attributes=["email"],
                ),
                "merged_records": [{"id": "p1", "email": "a@b.c"}],
            },
            "assembled",
        ),
        (
            response_lookup_incomplete,
            {
                "query": EntityQuery(
                    lookup={"name": "Paul Murphy"},
                    requested_attributes=["email"],
                ),
                "required_fields": ["employer"],
            },
            "lookup_incomplete",
        ),
    ],
)
def test_response_builders_set_outcome(
    builder,
    kwargs: dict,
    expected_outcome: str,
) -> None:
    response = builder(**kwargs)
    _assert_outcome(response, expected_outcome)
    payload = json.loads(response.model_dump_json())
    assert payload["outcome"] == expected_outcome
    assert "suggestions" in payload


@pytest.mark.smoke
def test_query_response_json_schema_includes_outcome_and_suggestions() -> None:
    schema = _neutral_json_schema(QueryResponse)
    props = schema.get("properties") or {}
    assert "outcome" in props
    assert "suggestions" in props
    assert "provenance" in props
    assert "total_matches" in props
    assert "delivery" in props
    assert schema.get("title") == "QueryResponse"
    description = schema.get("description") or ""
    assert "outcome" in description
    assert "suggestions" in description
    assert "provenance" in description
    assert "lookup_resolved" in description
    assert "total_matches" in description


@pytest.mark.smoke
def test_query_response_model_json_schema_includes_outcome_and_suggestions() -> None:
    schema = QueryResponse.model_json_schema()
    assert "outcome" in schema["properties"]
    assert "suggestions" in schema["properties"]
    assert "required_fields" in schema["properties"]

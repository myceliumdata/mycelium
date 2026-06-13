"""Smoke tests: QueryResponse outcome consistency across builders and MCP schema."""

from __future__ import annotations

import json

import pytest

from agents.responses import (
    response_assembled,
    response_entity_unknown,
    response_entity_unresolved,
    response_found,
    response_non_core,
    response_not_found,
)
from network.mvr import MvrPolicy
from models.state import EntityKeySuggestion, EntityQuery, IdentityRecord, QueryResponse
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
                "query": EntityQuery(entity_key="Ada"),
                "identity_records": [IdentityRecord(id="p1", name="Ada", employer="Lab")],
            },
            "found",
        ),
        (
            response_not_found,
            {"query": EntityQuery(entity_key="Missing")},
            "not_found",
        ),
        (
            response_entity_unresolved,
            {
                "query": EntityQuery(entity_key="Andrea Kalman"),
                "suggestions": [
                    EntityKeySuggestion(
                        entity_key="Andrea Kalmans",
                        id="s1",
                        name="Andrea Kalmans",
                        employer="Lontra Ventures",
                        score=0.92,
                    ),
                ],
            },
            "entity_key_unresolved",
        ),
        (
            response_non_core,
            {
                "query": EntityQuery(entity_key="Ada", requested_attributes=["email"]),
                "identity_records": [IdentityRecord(id="p1", name="Ada", employer="Lab")],
                "attributes": ["email"],
            },
            "assembled",
        ),
        (
            response_assembled,
            {
                "query": EntityQuery(entity_key="Ada", requested_attributes=["email"]),
                "merged_records": [{"id": "p1", "email": "a@b.c"}],
            },
            "assembled",
        ),
        (
            response_entity_unknown,
            {
                "query": EntityQuery(entity_key="Paul Murphy", requested_attributes=["email"]),
                "mvr": MvrPolicy(
                    bind_fields=["name", "employer"],
                    name_source="entity_key",
                    description="test",
                ),
            },
            "entity_unknown",
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
def test_entity_unresolved_empty_suggestions_falls_back_to_not_found() -> None:
    response = response_entity_unresolved(
        EntityQuery(entity_key="Nobody"),
        suggestions=[],
    )
    _assert_outcome(response, "not_found")
    assert response.suggestions == []


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

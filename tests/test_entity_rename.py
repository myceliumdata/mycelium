"""Smoke tests for MCP slice 1 — entity-neutral public vocabulary."""

from __future__ import annotations

import json

import pytest

from models.state import EntityQuery, QueryResponse, SeedRecord


def _collect_descriptions(schema: dict) -> list[str]:
    descriptions: list[str] = []
    for value in schema.values():
        if isinstance(value, dict):
            if "description" in value and isinstance(value["description"], str):
                descriptions.append(value["description"])
            descriptions.extend(_collect_descriptions(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    descriptions.extend(_collect_descriptions(item))
    return descriptions


@pytest.mark.smoke
def test_entity_query_schema_descriptions_are_neutral() -> None:
    schema = EntityQuery.model_json_schema()
    assert schema.get("title") == "EntityQuery"
    for description in _collect_descriptions(schema):
        assert "person" not in description.lower()


@pytest.mark.smoke
def test_query_response_schema_title() -> None:
    schema = QueryResponse.model_json_schema()
    assert schema.get("title") == "QueryResponse"


@pytest.mark.smoke
def test_seed_record_schema_title() -> None:
    schema = SeedRecord.model_json_schema()
    assert schema.get("title") == "SeedRecord"


@pytest.mark.smoke
def test_mcp_exposes_query_entity_tool() -> None:
    from mycelium_mcp import server

    assert hasattr(server, "query_entity")
    assert callable(server.query_entity)


@pytest.mark.smoke
def test_mcp_query_entity_round_trip_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import shutil
    from pathlib import Path

    from network.paths import NetworkPaths, apply_network_paths

    repo = Path(__file__).resolve().parent.parent
    root = tmp_path / "net"
    root.mkdir()
    shutil.copy(repo / "examples" / "networks" / "crm" / "seed.json", root / "seed.json")
    shutil.copy(repo / "examples" / "networks" / "crm" / "network.json", root / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(root / "entities.json"))
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    apply_network_paths(NetworkPaths.from_root(root))

    from network_helpers import import_seed_for_test

    import_seed_for_test(root / "seed.json")

    from mycelium_mcp.server import query_entity

    raw = query_entity(
        json.dumps({"entity_key": "Nichanan Kesonpat", "requested_attributes": []}),
    )
    payload = json.loads(raw)
    assert payload["results"]
    assert "entity_key" not in payload
    assert payload["results"][0]["name"] == "Nichanan Kesonpat"

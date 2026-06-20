"""Smoke tests: MVR redesign M9 — public CLI/MCP/example JSON migration."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.entity_registry import reset_entity_registry
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from graphs.core import reset_core_graph
from mycelium_mcp.server import _parse_query_payload, query_entity
from network.delivery import reset_delivery_store
from network_helpers import (
    import_seed_for_test,
    mock_email_research,
    register_contact_specialist,
)
from storage.core import reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"
EXAMPLE_QUERIES = EXAMPLE_CRM / "queries"


def _run_cli(monkeypatch: pytest.MonkeyPatch, *args: str) -> dict:
    import main as cli_main

    captured: list = []

    def _capture(response) -> None:
        captured.append(response)

    monkeypatch.setattr(cli_main, "_print_response", _capture)
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    code = cli_main.main(["query", *args])
    assert captured, "CLI did not emit a QueryResponse"
    return {"code": code, "response": captured[-1].model_dump()}


def _run_cli_public_json(monkeypatch: pytest.MonkeyPatch, *args: str) -> dict:
    """CLI client-visible JSON (``QueryResponse.public_json()``)."""
    import main as cli_main

    captured: list = []

    def _capture(response) -> None:
        captured.append(response)

    monkeypatch.setattr(cli_main, "_print_response", _capture)
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    code = cli_main.main(["query", *args])
    assert captured, "CLI did not emit a QueryResponse"
    payload = json.loads(captured[-1].public_json())
    return {"code": code, "payload": payload}


def _mcp_public_json(query_payload: dict) -> dict:
    """MCP client-visible JSON (``query_entity`` return string)."""
    return json.loads(query_entity(json.dumps(query_payload)))


@pytest.fixture
def crm_public_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()

    root = tmp_path / "crm"
    root.mkdir(parents=True, exist_ok=True)
    shutil.copy(EXAMPLE_CRM_SEED, root / "seed.json")
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    shutil.copy(EXAMPLE_CRM / "network.json", root / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(root / "test.db"))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(root / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(root / "categories.json"))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(root / "entities.json"))
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(root / "deliveries.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(root / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(root / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(root / "agent_data"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_category_tree()
    get_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    register_contact_specialist()
    import_seed_for_test(root / "seed.json")
    reset_core_graph()
    return root


@pytest.mark.smoke
def test_example_batch_resolve_json_is_valid_target_step1() -> None:
    payload = json.loads((EXAMPLE_QUERIES / "01-resolve-batch.json").read_text())
    query, _thread = _parse_query_payload(json.dumps(payload))
    assert query.lookup == {"employer": "645 Ventures"}
    assert query.requested_attributes == ["email"]
    assert not (query.id or "").strip()


@pytest.mark.smoke
def test_cli_lookup_then_deliver_roundtrip(
    crm_public_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_public_env
    step1 = _run_cli(
        monkeypatch,
        "--network-dir",
        str(crm_public_env),
        "--lookup-json",
        '{"name": "Nichanan Kesonpat", "employer": "1k(x)"}',
    )
    assert step1["response"]["outcome"] == "lookup_resolved"
    delivery_id = step1["response"]["delivery"]["delivery_id"]

    step2 = _run_cli(
        monkeypatch,
        "--network-dir",
        str(crm_public_env),
        "--delivery-id",
        delivery_id,
    )
    assert step2["response"]["outcome"] == "found"
    assert step2["response"]["results"][0]["name"] == "Nichanan Kesonpat"


@pytest.mark.smoke
def test_mcp_rejects_legacy_entity_key_only(
    crm_public_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_public_env
    with pytest.raises(ValueError, match="entity_key/binding removed"):
        _parse_query_payload(json.dumps({"entity_key": "Nichanan Kesonpat"}))


@pytest.mark.smoke
def test_mcp_example_batch_fixture_roundtrip(
    crm_public_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_public_env
    mock_email_research(monkeypatch)
    resolve_json = (EXAMPLE_QUERIES / "01-resolve-batch.json").read_text()
    raw_step1 = query_entity(resolve_json)
    step1 = json.loads(raw_step1)
    assert step1["outcome"] == "lookup_resolved"
    assert step1["total_matches"] == 3
    delivery_id = step1["delivery"]["delivery_id"]

    deliver_payload = json.loads((EXAMPLE_QUERIES / "02-deliver-batch.json").read_text())
    deliver_payload["delivery_id"] = delivery_id
    raw_step2 = query_entity(json.dumps(deliver_payload))
    step2 = json.loads(raw_step2)
    assert step2["outcome"] == "assembled"
    assert len(step2["results"]) == 3


@pytest.mark.smoke
def test_mcp_create_pending_wire_json(
    crm_public_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_public_env
    payload = _mcp_public_json(
        {"lookup": {"name": "Road Runner", "employer": "Acme Corp"}},
    )
    assert payload["outcome"] == "lookup_resolved"
    assert payload["total_matches"] == 0
    assert payload["delivery"]["create_on_deliver"] is True
    assert "step 2 will create" in payload["message"]
    assert "quote" not in payload


@pytest.mark.smoke
def test_mcp_existing_match_wire_json(
    crm_public_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_public_env
    payload = _mcp_public_json(
        {
            "lookup": {
                "name": "Nichanan Kesonpat",
                "employer": "1k(x)",
            },
        },
    )
    assert payload["outcome"] == "lookup_resolved"
    assert payload["total_matches"] == 1
    assert "create_on_deliver" not in payload["delivery"]
    assert payload["delivery"].get("create_on_deliver") is not False
    assert "1 registry match" in payload["message"]
    assert "step 2" in payload["message"]
    assert "quote" not in payload


@pytest.mark.smoke
def test_cli_create_pending_public_json(
    crm_public_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_public_env
    result = _run_cli_public_json(
        monkeypatch,
        "--network-dir",
        str(crm_public_env),
        "--lookup-json",
        '{"name": "Road Runner", "employer": "Acme Corp"}',
    )
    payload = result["payload"]
    assert payload["outcome"] == "lookup_resolved"
    assert payload["total_matches"] == 0
    assert payload["delivery"]["create_on_deliver"] is True
    assert "step 2 will create" in payload["message"]
    assert "quote" not in payload


@pytest.mark.smoke
def test_mcp_employer_fuzzy_public_json_omits_person_fields(
    crm_public_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_public_env
    payload = _mcp_public_json({"lookup": {"employer": "645 Venture"}})
    assert payload["outcome"] == "lookup_suggested"
    suggestion = payload["suggestions"][0]
    assert suggestion["suggested_lookup"] == {"employer": "645 Ventures"}
    assert suggestion["reason"] == "fuzzy_bind_field_match"
    assert "entity_key" not in suggestion
    assert "id" not in suggestion
    assert "name" not in suggestion


@pytest.mark.smoke
def test_cli_existing_match_public_json(
    crm_public_env: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_public_env
    result = _run_cli_public_json(
        monkeypatch,
        "--network-dir",
        str(crm_public_env),
        "--lookup-json",
        '{"name": "Nichanan Kesonpat", "employer": "1k(x)"}',
    )
    payload = result["payload"]
    assert payload["outcome"] == "lookup_resolved"
    assert payload["total_matches"] == 1
    assert "create_on_deliver" not in payload["delivery"]
    assert payload["delivery"].get("create_on_deliver") is not False
    assert "1 registry match" in payload["message"]
    assert "quote" not in payload

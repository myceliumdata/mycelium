"""CLI smoke tests for metering negotiation flags (Slice 12 scaffolding)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_DEMO_SCRIPT = REPO_ROOT / "bin" / "demo-metering-negotiation"
_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python3"
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


def _run_cli_query(monkeypatch: pytest.MonkeyPatch, *args: str) -> tuple[int, dict[str, Any]]:
    """Invoke ``main.query`` in-process (research mocks apply)."""
    import main as cli_main

    captured: list[Any] = []

    def _capture(response: Any) -> None:
        captured.append(response)

    monkeypatch.setattr(cli_main, "_print_response", _capture)
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    code = cli_main.main(["query", *args])
    assert captured, "CLI did not emit a QueryResponse"
    return code, captured[-1].model_dump()


def _write_metering_network_json(path: Path) -> None:
    data = json.loads((EXAMPLE_CRM / "network.json").read_text(encoding="utf-8"))
    metering = dict(data.get("metering") or {})
    metering["enabled"] = True
    metering["payment"] = {
        "enabled": False,
        "provider": "mock",
        "require_paid_before_accept": True,
    }
    data["metering"] = metering
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _mock_email_research(monkeypatch: pytest.MonkeyPatch) -> None:
    from tools.research import ResearchRunResult
    from versioned_storage_fixtures import versioned_found

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        llm: Any | None = None,
    ) -> ResearchRunResult:
        _ = category, specialist_name, context, llm
        from agents.specialists.base import SpecialistStorage

        storage = SpecialistStorage(category=category)
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        for field in target_fields:
            rec[field] = versioned_found(
                at=now,
                value="paul.murphy@acme.example",
                confidence=0.9,
                sources=["https://example.com/paul"],
                category=category,
                specialist_name=specialist_name,
            )
        storage.save(data)
        return ResearchRunResult(fields_updated=list(target_fields), tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)


@pytest.fixture
def metering_cli_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, str]:
    root = tmp_path / "metering-net"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM_SEED, root / "seed.json")
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    _write_metering_network_json(root / "network.json")

    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(root / "test.db"))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(root / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    from agents.classification import get_category_tree, reset_category_tree
    from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
    from agents.registry import reset_agent_registry
    from agents.entity_registry import reset_entity_registry
    from graphs.core import reset_core_graph
    from network_helpers import import_seed_for_test
    from network.paths import NetworkPaths, apply_network_paths
    from storage.core import reset_storage

    apply_network_paths(NetworkPaths.from_root(root))
    reset_storage()
    reset_entity_registry()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    reset_core_graph()

    get_category_tree()
    factory = get_agent_factory()
    factory.create_specialist(
        "contact",
        "contact_specialist",
        "Direct contact info",
        examples=["email", "phone"],
        auto_commit=False,
    )
    import_seed_for_test(root / "seed.json")
    reset_core_graph()

    _mock_email_research(monkeypatch)

    return {
        "MYCELIUM_NETWORK_ROOT": str(root),
        "MYCELIUM_USE_SYNC_CHECKPOINTER": "1",
        "MYCELIUM_NETWORK": "",
    }


@pytest.mark.smoke
def test_cli_query_binding_and_quote_id(
    metering_cli_env: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = metering_cli_env
    root = env["MYCELIUM_NETWORK_ROOT"]
    lookup = '{"name": "Paul Murphy", "employer": "Acme Corp"}'

    _, quote_payload = _run_cli_query(
        monkeypatch,
        "--network-dir",
        root,
        "--lookup-json",
        lookup,
        "--attributes",
        "email",
    )
    assert quote_payload["outcome"] == "quote_required"
    assert quote_payload["quote"] is not None
    quote_id = quote_payload["quote"]["quote_id"]
    delivery_id = quote_payload["delivery"]["delivery_id"]

    _, accept_payload = _run_cli_query(
        monkeypatch,
        "--network-dir",
        root,
        "--delivery-id",
        delivery_id,
        "--quote-id",
        quote_id,
    )
    assert accept_payload["outcome"] == "assembled"


def _warm_metering_network(root: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pre-quote and research email so subprocess demo can assemble without API keys."""
    from graphs.core import reset_core_graph, run_query
    from models.state import EntityQuery

    _mock_email_research(monkeypatch)
    reset_core_graph()
    lookup = {"name": "Paul Murphy", "employer": "Acme Corp"}
    quoted = run_query(
        EntityQuery(lookup=lookup, requested_attributes=["email"]),
    )
    assert quoted.quote is not None
    assert quoted.delivery is not None
    run_query(
        EntityQuery(
            delivery_id=quoted.delivery.delivery_id,
            quote_id=quoted.quote["quote_id"],
        ),
    )


@pytest.mark.smoke
def test_demo_metering_negotiation_script(
    metering_cli_env: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = metering_cli_env["MYCELIUM_NETWORK_ROOT"]
    _warm_metering_network(root, monkeypatch)

    python = str(_VENV_PYTHON) if _VENV_PYTHON.is_file() else sys.executable
    env = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT / "src"),
        "MYCELIUM_NETWORK_ROOT": root,
        "MYCELIUM_NETWORK": "",
        "LANGCHAIN_TRACING_V2": "false",
    }
    env.pop("MYCELIUM_USE_SYNC_CHECKPOINTER", None)

    result = subprocess.run(
        [python, str(_DEMO_SCRIPT), "--network-dir", root, "--json-only"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    output = result.stdout
    assert "quote_required" in output
    assert "assembled" in output

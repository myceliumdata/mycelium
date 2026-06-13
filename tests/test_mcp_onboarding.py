"""Smoke tests for MCP slice 2 — guide, describe_network, capabilities builder."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from network.example import copy_example_network
from network.introspection import build_network_capabilities, format_mcp_instructions
from network.paths import NetworkPaths, apply_network_paths

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"


def _configure_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(root.parent / "missing.json"))
    apply_network_paths(NetworkPaths.from_root(root))


@pytest.mark.smoke
def test_build_network_capabilities_with_guide_and_ontology(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "net"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "guide.md", root / "guide.md")
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    _configure_root(monkeypatch, root)

    caps = build_network_capabilities()
    assert "binding" in caps["policy"]["query"]["optional_fields"]

    assert caps["guide_present"] is True
    assert "investor information" in (caps["guide"] or "")
    assert caps["ontology"]["present"] is True
    assert len(caps["ontology"]["categories"]) == 6
    assert caps["ontology"]["categories"][0]["name"]
    assert caps["ontology"]["categories"][0]["description"]
    assert caps["policy"]["query"]["tool"] == "query_entity"
    assert "response_provenance" in caps["policy"]["query"]
    assert "target_protocol" in caps["policy"]["query"]
    assert caps["policy"]["query"]["target_protocol"]["shipping"]
    assert "guide_note" not in caps


@pytest.mark.smoke
def test_build_network_capabilities_missing_guide(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "bare"
    root.mkdir()
    _configure_root(monkeypatch, root)

    caps = build_network_capabilities()
    assert "binding" in caps["policy"]["query"]["optional_fields"]

    assert caps["guide_present"] is False
    assert caps["guide"] is None
    assert caps["guide_note"] == "Network author has not provided guide.md yet."
    assert caps["ontology"]["present"] is False


@pytest.mark.smoke
def test_format_mcp_instructions_references_describe_network() -> None:
    text = format_mcp_instructions(
        {
            "display_name": "CRM example",
            "network_name": "crm",
        },
    )
    assert "describe_network" in text
    assert "query_entity" in text
    assert "CRM example" in text


@pytest.mark.smoke
def test_describe_network_returns_parseable_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "net"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    shutil.copy(EXAMPLE_CRM / "network.json", root / "network.json")
    shutil.copy(EXAMPLE_CRM / "guide.md", root / "guide.md")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")

    from mycelium_mcp.server import describe_network

    payload = json.loads(describe_network())
    assert "policy" in payload
    assert "ontology" in payload
    assert payload["guide_present"] is True
    assert "guide" in payload


@pytest.mark.smoke
def test_list_specialist_routing_not_exposed() -> None:
    import mycelium_mcp.server as server

    assert not hasattr(server, "list_specialist_routing")
    assert hasattr(server, "describe_network")


@pytest.mark.smoke
def test_health_check_lightweight_tool_still_ok(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "net"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    shutil.copy(EXAMPLE_CRM / "network.json", root / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")

    from mycelium_mcp.server import health_check

    payload = json.loads(health_check())
    assert payload["checks"].get("lightweight_tool") == "ok"


@pytest.mark.smoke
def test_refresh_copies_guide_md(tmp_path: Path) -> None:
    target = tmp_path / "live-crm"
    copied = copy_example_network("crm", target)
    assert "guide.md" in copied
    assert (target / "guide.md").is_file()

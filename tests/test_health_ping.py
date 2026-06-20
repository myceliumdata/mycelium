"""Smoke tests for per-network MCP health_check ping lookup."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from network.health_ping import resolve_health_ping_lookup
from network.paths import NetworkPaths, apply_network_paths
from network_helpers import import_seed_for_test

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_BASEBALL = REPO_ROOT / "examples" / "networks" / "baseball"
EXAMPLE_EMPTY_CRM = REPO_ROOT / "examples" / "networks" / "empty-crm"


@pytest.mark.smoke
def test_resolve_health_ping_lookup_crm_example() -> None:
    paths = NetworkPaths.from_root(EXAMPLE_CRM)
    lookup = resolve_health_ping_lookup(paths=paths)
    assert lookup == {"name": "Nichanan Kesonpat", "employer": "1k(x)"}


@pytest.mark.smoke
def test_resolve_health_ping_lookup_baseball_example() -> None:
    paths = NetworkPaths.from_root(EXAMPLE_BASEBALL)
    lookup = resolve_health_ping_lookup(paths=paths)
    assert lookup == {"player": "Hank Aaron"}


@pytest.mark.smoke
def test_resolve_health_ping_lookup_missing_returns_none(tmp_path: Path) -> None:
    root = tmp_path / "net"
    root.mkdir()
    shutil.copy(EXAMPLE_EMPTY_CRM / "network.json", root / "network.json")
    paths = NetworkPaths.from_root(root)
    assert resolve_health_ping_lookup(paths=paths) is None


@pytest.mark.smoke
def test_health_check_ping_ok_for_crm_seed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "crm_copy"
    shutil.copytree(
        EXAMPLE_CRM,
        root,
        ignore=shutil.ignore_patterns("prepare_seed.py"),
    )
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    apply_network_paths(NetworkPaths.from_root(root))
    import_seed_for_test(root / "seed.json")

    from mycelium_mcp.server import health_check

    payload = json.loads(health_check())
    assert payload["checks"]["ping_query"] == "ok"


@pytest.mark.smoke
def test_health_check_ping_skipped_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "empty_copy"
    shutil.copytree(EXAMPLE_EMPTY_CRM, root)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")

    from mycelium_mcp.server import health_check

    payload = json.loads(health_check())
    assert payload["checks"]["ping_query"].startswith("skipped:")
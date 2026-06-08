"""End-to-end integration tests for the networks stack (Phases 1–4)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

from network_helpers import NETWORK_PATH_ENV_KEYS, clear_network_path_env
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.paths import NetworkPaths, apply_network_paths, resolve_network_root
from network.registry import register_network

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python3"
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", text)


@pytest.fixture(autouse=True)
def _sync_checkpointer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Match CLI/MCP: in-process run_query needs sync checkpointer across calls."""
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")


def _reset_runtime_singletons() -> None:
    from agents.classification import reset_category_tree
    from agents.context import reset_context_builder
    from agents.core_identity import reset_core_identity
    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry
    from agents.seed import reset_seed_data
    from storage.core import reset_storage

    for reset_fn in (
        reset_core_graph,
        reset_storage,
        reset_seed_data,
        reset_context_builder,
        reset_core_identity,
        reset_category_tree,
        reset_agent_registry,
        reset_agent_factory,
    ):
        try:
            reset_fn()
        except Exception:
            pass


def _write_network_seed(root: Path, people: list[dict[str, str | None]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "seed.json").write_text(
        json.dumps({"people": people}, indent=2) + "\n",
        encoding="utf-8",
    )


def _isolated_registry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    config = tmp_path / "networks.json"
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(config))
    clear_network_path_env(monkeypatch)
    return config


def _isolated_network_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    network_root: Path | None = None,
    framework_root: Path | None = None,
) -> Path:
    """Isolate registry and legacy path vars; optionally pin an active network root."""
    config = _isolated_registry(monkeypatch, tmp_path)
    if framework_root is not None:
        monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(framework_root))
    if network_root is not None:
        monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(network_root))
    return config


def _apply_resolved_network(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    _isolated_registry(monkeypatch, root.parent)  # no-op if already set
    apply_network_paths(NetworkPaths.from_root(root))
    _reset_runtime_singletons()


def _unique_thread_id(label: str) -> str:
    return f"network-integration-{label}-{uuid.uuid4()}"


def _run_mycelium_cli(
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    python = str(_VENV_PYTHON) if _VENV_PYTHON.is_file() else sys.executable
    cmd = [python, "-m", "main", *args]
    merged = os.environ.copy()
    for key in NETWORK_PATH_ENV_KEYS:
        merged.pop(key, None)
    merged.pop("MYCELIUM_NETWORK", None)
    if env:
        merged.update(env)
    merged["PYTHONPATH"] = str(REPO_ROOT / "src")
    merged["LANGCHAIN_TRACING_V2"] = "false"
    merged["NO_COLOR"] = "1"
    merged["FORCE_COLOR"] = "0"
    merged.setdefault("COLUMNS", "240")
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=merged,
        capture_output=True,
        text=True,
        check=False,
    )


def _parse_cli_json(stdout: str) -> dict[str, Any]:
    lines = [
        line
        for line in _strip_ansi(stdout).strip().splitlines()
        if not line.strip().startswith("LangSmith trace:")
    ]
    text = "\n".join(lines).strip()
    if not text:
        msg = "empty CLI stdout"
        raise ValueError(msg)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        msg = "no JSON object in CLI stdout"
        raise ValueError(msg)
    blob = text[start : end + 1]
    # Rich may soft-wrap long string values (e.g. trace_id URLs, thread_id).
    blob = re.sub(r':\s*\n\s*"', ': "', blob)
    blob = re.sub(r'(?<=[^\\])"\s*\n\s*"', '" "', blob)
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        compact = re.sub(r"\n\s*", " ", blob)
        return json.loads(compact)


# --- 1. Path resolver ---


@pytest.mark.smoke
def test_no_network_configured_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(tmp_path / "framework"))
    with pytest.raises(ValueError, match="refresh-example-network"):
        resolve_network_root()


@pytest.mark.smoke
def test_mcp_bootstrap_uses_mycelium_network_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    net = tmp_path / "mcp_net"
    _write_network_seed(net, [{"name": "MCP Person", "employer": "MCP Co"}])
    _isolated_network_env(monkeypatch, tmp_path, network_root=net)

    from mycelium_mcp.server import _bootstrap

    _bootstrap()
    assert os.environ["MYCELIUM_SEED_PATH"] == str(net / "seed.json")
    assert os.environ["MYCELIUM_NETWORK_ROOT"] == str(net.resolve())


@pytest.mark.full
def test_network_dir_overrides_registry_default_query(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    default_root = tmp_path / "default_net"
    override_root = tmp_path / "override_net"
    _write_network_seed(
        default_root,
        [{"name": "Default Only", "employer": "Default Co"}],
    )
    _write_network_seed(
        override_root,
        [{"name": "Override Only", "employer": "Override Co"}],
    )
    register_network("def", default_root, default=True)

    root = resolve_network_root(cli_network_dir=str(override_root))
    apply_network_paths(NetworkPaths.from_root(root))
    _reset_runtime_singletons()

    response = run_query(
        EntityQuery(entity_key="Override Only"),
        thread_id=_unique_thread_id("override"),
    )
    assert len(response.results) == 1
    assert response.results[0]["name"] == "Override Only"


# --- 2. Registry + default ---


@pytest.mark.full
def test_query_via_registered_network_name(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    net = tmp_path / "named"
    _write_network_seed(net, [{"name": "Registry Person", "employer": "Reg Co"}])
    register_network("my_net", net, default=True)

    root = resolve_network_root(cli_network_name="my_net")
    apply_network_paths(NetworkPaths.from_root(root))
    _reset_runtime_singletons()

    response = run_query(
        EntityQuery(entity_key="Registry Person"),
        thread_id=_unique_thread_id("named"),
    )
    assert response.results[0]["employer"] == "Reg Co"


@pytest.mark.full
def test_plain_query_uses_default_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    default_root = tmp_path / "default"
    other_root = tmp_path / "other"
    _write_network_seed(default_root, [{"name": "Default Person", "employer": "D"}])
    _write_network_seed(other_root, [{"name": "Other Person", "employer": "O"}])
    register_network("primary", default_root, default=True)
    register_network("secondary", other_root)

    root = resolve_network_root()
    apply_network_paths(NetworkPaths.from_root(root))
    _reset_runtime_singletons()

    response = run_query(
        EntityQuery(entity_key="Default Person"),
        thread_id=_unique_thread_id("default"),
    )
    assert len(response.results) == 1
    assert response.results[0]["name"] == "Default Person"


@pytest.mark.full
def test_cli_network_register_list_use_and_query(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = _isolated_registry(monkeypatch, tmp_path)
    net_a = tmp_path / "a"
    net_b = tmp_path / "b"
    _write_network_seed(net_a, [{"name": "Alpha Person", "employer": "A"}])
    _write_network_seed(net_b, [{"name": "Beta Person", "employer": "B"}])
    env = {"MYCELIUM_NETWORKS_CONFIG": str(config), "MYCELIUM_FRAMEWORK_ROOT": str(tmp_path / "fw")}

    reg_a = _run_mycelium_cli(
        "network",
        "register",
        "alpha",
        "--root",
        str(net_a),
        "--default",
        env=env,
    )
    assert reg_a.returncode == 0, reg_a.stderr or reg_a.stdout

    reg_b = _run_mycelium_cli(
        "network",
        "register",
        "beta",
        "--root",
        str(net_b),
        env=env,
    )
    assert reg_b.returncode == 0, reg_b.stderr or reg_b.stdout

    listing = _run_mycelium_cli("network", "list", env=env)
    assert listing.returncode == 0
    plain_list = _strip_ansi(listing.stdout)
    assert "alpha" in plain_list
    assert "beta" in plain_list
    assert "(default)" in plain_list

    use_b = _run_mycelium_cli("network", "use", "beta", env=env)
    assert use_b.returncode == 0, use_b.stderr or use_b.stdout

    query = _run_mycelium_cli(
        "query",
        "--entity-key",
        "Beta Person",
        "--thread-id",
        _unique_thread_id("cli-default"),
        env=env,
    )
    assert query.returncode == 0, query.stderr or query.stdout
    payload = _parse_cli_json(query.stdout)
    assert payload["results"][0]["name"] == "Beta Person"

    query_named = _run_mycelium_cli(
        "query",
        "--network",
        "alpha",
        "--entity-key",
        "Alpha Person",
        "--thread-id",
        _unique_thread_id("cli-named"),
        env=env,
    )
    assert query_named.returncode == 0, query_named.stderr or query_named.stdout
    named_payload = _parse_cli_json(query_named.stdout)
    assert named_payload["results"][0]["name"] == "Alpha Person"


# --- 3. Multi-network isolation ---


@pytest.mark.full
def test_two_network_roots_isolated_query_results(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolated_registry(monkeypatch, tmp_path)
    net_a = tmp_path / "iso_a"
    net_b = tmp_path / "iso_b"
    _write_network_seed(net_a, [{"name": "Iso A", "employer": "Co A"}])
    _write_network_seed(net_b, [{"name": "Iso B", "employer": "Co B"}])

    apply_network_paths(NetworkPaths.from_root(net_a))
    _reset_runtime_singletons()
    resp_a = run_query(EntityQuery(entity_key="Iso A"), thread_id=_unique_thread_id("iso-a"))
    assert resp_a.results[0]["employer"] == "Co A"
    assert run_query(EntityQuery(entity_key="Iso B"), thread_id=_unique_thread_id("iso-a-miss")).results == []

    apply_network_paths(NetworkPaths.from_root(net_b))
    _reset_runtime_singletons()
    reset_core_graph()
    resp_b = run_query(EntityQuery(entity_key="Iso B"), thread_id=_unique_thread_id("iso-b"))
    assert resp_b.results[0]["employer"] == "Co B"
    assert run_query(EntityQuery(entity_key="Iso A"), thread_id=_unique_thread_id("iso-b-miss")).results == []


# --- 4. Example network bootstrap ---


@pytest.mark.full
def test_refresh_example_register_and_query_nichanan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = _isolated_registry(monkeypatch, tmp_path)
    target = tmp_path / "crm_copy"
    refresh_script = REPO_ROOT / "bin" / "refresh-example-network"
    refresh_env = os.environ.copy()
    refresh_env["MYCELIUM_NETWORKS_CONFIG"] = str(config)
    copy = subprocess.run(
        [
            sys.executable,
            str(refresh_script),
            "crm",
            "--root",
            str(target),
            "--yes",
        ],
        cwd=REPO_ROOT,
        env=refresh_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert copy.returncode == 0, copy.stderr or copy.stdout
    assert (target / "seed.json").is_file()

    env = {"MYCELIUM_NETWORKS_CONFIG": str(config), "MYCELIUM_FRAMEWORK_ROOT": str(tmp_path / "fw")}
    query = _run_mycelium_cli(
        "query",
        "--network",
        "crm",
        "--entity-key",
        "Nichanan Kesonpat",
        "--thread-id",
        _unique_thread_id("example"),
        env=env,
    )
    assert query.returncode == 0, query.stderr or query.stdout
    payload = _parse_cli_json(query.stdout)
    assert payload["results"][0]["name"] == "Nichanan Kesonpat"
    assert payload["results"][0]["employer"] == "1k(x)"


# --- 5. MCP ---


@pytest.mark.smoke
def test_health_check_reports_network_metadata_for_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import shutil

    net_root = tmp_path / "health_net"
    shutil.copytree(EXAMPLE_CRM, net_root, ignore=shutil.ignore_patterns("prepare_seed.py"))
    _isolated_network_env(monkeypatch, tmp_path, network_root=net_root)

    from mycelium_mcp.server import health_check

    payload = json.loads(health_check())
    info = payload["info"]
    assert info["network_root"] == str(net_root.resolve())
    assert info["network_name"] == "crm"
    assert info["network_display_name"] == "CRM example"


@pytest.mark.full
def test_mcp_query_entity_reads_active_network_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    net = tmp_path / "mcp_query_net"
    _write_network_seed(net, [{"name": "MCP Query Person", "employer": "MQ"}])
    _isolated_network_env(monkeypatch, tmp_path, network_root=net)
    _reset_runtime_singletons()

    from mycelium_mcp.server import query_entity

    raw = query_entity(
        json.dumps(
            {
                "entity_key": "MCP Query Person",
                "thread_id": _unique_thread_id("mcp-query"),
            },
        ),
    )
    payload = json.loads(raw)
    assert payload["results"][0]["name"] == "MCP Query Person"
    assert payload["results"][0]["employer"] == "MQ"


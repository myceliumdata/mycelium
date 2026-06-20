"""Pytest fixtures for opt-in live gate scenarios."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

LIVE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LIVE_DIR.parent.parent
RUNS_DIR = REPO_ROOT / "docs" / "manual-checks" / "runs"

if str(LIVE_DIR) not in sys.path:
    sys.path.insert(0, str(LIVE_DIR))

from gate_runner import (  # noqa: E402
    ScenarioResult,
    filter_scenarios,
    load_anchors,
    load_catalog,
    load_networks_registry,
    reset_query_runtime,
)
from network.paths import NetworkPaths, apply_network_paths  # noqa: E402


@pytest.fixture(scope="session")
def live_gate_network_name() -> str:
    name = os.getenv("LIVE_GATE_NETWORK", "").strip()
    if not name:
        pytest.skip("LIVE_GATE_NETWORK not set (run via ./bin/gate-live)")
    return name


@pytest.fixture(scope="session")
def live_gate_network_entry(live_gate_network_name: str):
    registry = load_networks_registry()
    if live_gate_network_name not in registry:
        pytest.skip(f"unknown LIVE_GATE_NETWORK={live_gate_network_name!r}")
    return registry[live_gate_network_name]


@pytest.fixture(scope="session")
def live_gate_root(live_gate_network_entry) -> Path:
    override = os.getenv("MYCELIUM_NETWORK_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return live_gate_network_entry.default_root


@pytest.fixture(scope="session", autouse=True)
def _configure_live_gate_paths(live_gate_root: Path, live_gate_network_entry) -> None:
    if not live_gate_root.is_dir():
        pytest.skip(f"network root missing: {live_gate_root}")
    apply_network_paths(NetworkPaths.from_root(live_gate_root))
    reset_query_runtime()


@pytest.fixture(scope="session")
def live_gate_phases() -> set[str] | None:
    raw = os.getenv("LIVE_GATE_PHASE", "").strip()
    if not raw:
        return None
    phases: set[str] = set()
    for chunk in raw.replace(",", " ").split():
        if chunk.strip():
            phases.add(chunk.strip())
    return phases or None


@pytest.fixture(scope="session")
def live_gate_session_context(live_gate_root: Path) -> dict:
    return {"_network_root": live_gate_root}


@pytest.fixture(scope="session")
def live_gate_anchors(live_gate_network_entry) -> dict:
    return load_anchors(live_gate_network_entry.anchors_path)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "scenario_id" not in metafunc.fixturenames:
        return
    network = os.getenv("LIVE_GATE_NETWORK", "").strip()
    if not network:
        return
    registry = load_networks_registry()
    entry = registry.get(network)
    if entry is None:
        return
    phases_raw = os.getenv("LIVE_GATE_PHASE", "").strip()
    phases: set[str] | None = None
    if phases_raw:
        phases = {
            chunk.strip()
            for chunk in phases_raw.replace(",", " ").split()
            if chunk.strip()
        }
    scenarios = filter_scenarios(load_catalog(entry.catalog_path), phases=phases)
    metafunc.parametrize("scenario_id", [item.id for item in scenarios])


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    network = os.getenv("LIVE_GATE_NETWORK", "").strip()
    if not network:
        return
    report_items: list[dict] = []
    for item in session.items:
        if not hasattr(item, "live_gate_result"):
            continue
        result: ScenarioResult = item.live_gate_result
        report_items.append(
            {
                "id": result.id,
                "phase": result.phase,
                "passed": result.passed,
                "skipped": result.skipped,
                "detail": result.detail,
            },
        )
    if not report_items:
        return
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RUNS_DIR / f"{ts}-{network}-live-gate.json"
    payload = {
        "network": network,
        "network_root": os.getenv("MYCELIUM_NETWORK_ROOT", ""),
        "phases": os.getenv("LIVE_GATE_PHASE", ""),
        "exitstatus": exitstatus,
        "scenarios": report_items,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

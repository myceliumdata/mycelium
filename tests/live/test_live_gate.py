"""Opt-in live gate scenarios — run via ./bin/gate-live only."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

LIVE_DIR = Path(__file__).resolve().parent
if str(LIVE_DIR) not in sys.path:
    sys.path.insert(0, str(LIVE_DIR))

from gate_runner import filter_scenarios, load_catalog, run_scenario  # noqa: E402
from graphs.core import reset_core_graph  # noqa: E402


@pytest.mark.live_gate
def test_live_gate_scenario(
    scenario_id: str,
    live_gate_network_entry,
    live_gate_anchors,
    live_gate_session_context,
    live_gate_phases,
    request: pytest.FixtureRequest,
) -> None:
    scenarios = filter_scenarios(
        load_catalog(live_gate_network_entry.catalog_path),
        phases=live_gate_phases,
    )
    spec = next(item for item in scenarios if item.id == scenario_id)
    reset_core_graph()
    result = run_scenario(
        spec,
        anchors=live_gate_anchors,
        context=live_gate_session_context,
    )
    request.node.live_gate_result = result  # type: ignore[attr-defined]
    if result.skipped:
        pytest.skip(result.detail)
    assert result.passed, result.detail

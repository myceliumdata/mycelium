"""Unit tests for live gate runner (smoke-safe, no deployed roots)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

LIVE_DIR = Path(__file__).resolve().parent / "live"
if str(LIVE_DIR) not in sys.path:
    sys.path.insert(0, str(LIVE_DIR))

import gate_runner as gr  # noqa: E402


@pytest.mark.smoke
def test_load_networks_registry_has_four_networks() -> None:
    registry = gr.load_networks_registry()
    assert set(registry) == {"baseball", "crm", "crm-metering", "empty-crm"}


@pytest.mark.smoke
def test_load_catalog_baseball_has_minimum_scenarios() -> None:
    entry = gr.load_networks_registry()["baseball"]
    scenarios = gr.load_catalog(entry.catalog_path)
    assert len(scenarios) >= 15
    phases = {item.phase for item in scenarios}
    assert phases >= {"preflight", "identity", "m2", "derive", "infra"}


@pytest.mark.smoke
def test_filter_scenarios_by_phase() -> None:
    entry = gr.load_networks_registry()["crm"]
    scenarios = gr.load_catalog(entry.catalog_path)
    filtered = gr.filter_scenarios(scenarios, phases={"protocol"})
    assert filtered
    assert all(item.phase == "protocol" for item in filtered)


@pytest.mark.smoke
def test_resolve_template_anchors() -> None:
    anchors = {"player": "Hank Aaron", "persons": {"nichanan": {"name": "Nichanan"}}}
    resolved = gr._resolve_template(
        {"lookup": {"player": "{{ anchors.player }}"}},
        anchors=anchors,
        context={},
    )
    assert resolved["lookup"]["player"] == "Hank Aaron"


@pytest.mark.smoke
def test_load_anchors_baseball_json() -> None:
    entry = gr.load_networks_registry()["baseball"]
    anchors = gr.load_anchors(entry.anchors_path)
    assert anchors["career_hr"] == 755
    assert anchors["career_avg"] == 0.305


@pytest.mark.smoke
def test_format_summary_table_includes_header() -> None:
    results = [
        gr.ScenarioResult(
            id="demo",
            phase="preflight",
            passed=True,
            skipped=False,
            detail="ok",
        ),
    ]
    table = gr.format_summary_table(results)
    assert "demo" in table
    assert "PASS" in table


@pytest.mark.smoke
def test_catalog_yaml_files_exist() -> None:
    for name in (
        "catalogs/baseball.yaml",
        "catalogs/crm.yaml",
        "catalogs/crm_metering.yaml",
        "catalogs/empty_crm.yaml",
        "networks.yaml",
    ):
        assert (LIVE_DIR / name).is_file()


@pytest.mark.smoke
def test_crm_seed_anchor_json() -> None:
    path = LIVE_DIR / "anchors" / "crm_seed_v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["seed_count"] == 15
    assert data["persons"]["batch_match_count"] == 3

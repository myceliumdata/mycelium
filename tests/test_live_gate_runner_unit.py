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
import assertions as live_assertions  # noqa: E402
from assertions import check_assertions  # noqa: E402


@pytest.mark.smoke
def test_load_networks_registry_has_four_networks() -> None:
    registry = gr.load_networks_registry()
    assert set(registry) == {"baseball", "crm", "crm-metering", "empty-crm"}


@pytest.mark.smoke
def test_baseball_fresh_derive_before_gate_flag() -> None:
    registry = gr.load_networks_registry()
    assert registry["baseball"].fresh_derive_before_gate is True
    assert registry["crm"].fresh_derive_before_gate is False
    assert registry["crm-metering"].fresh_derive_before_gate is False
    assert registry["empty-crm"].fresh_derive_before_gate is False


@pytest.mark.smoke
def test_should_fresh_derive_all_phases_baseball_default() -> None:
    entry = gr.load_networks_registry()["baseball"]
    assert gr.should_fresh_derive(
        network="baseball",
        entry=entry,
        phases=None,
        fresh_derive_flag=False,
        no_fresh_derive=False,
    )


@pytest.mark.smoke
def test_should_fresh_derive_m2_only_false() -> None:
    entry = gr.load_networks_registry()["baseball"]
    assert not gr.should_fresh_derive(
        network="baseball",
        entry=entry,
        phases={"m2"},
        fresh_derive_flag=False,
        no_fresh_derive=False,
    )


@pytest.mark.smoke
def test_should_fresh_derive_no_fresh_derive_false() -> None:
    entry = gr.load_networks_registry()["baseball"]
    assert not gr.should_fresh_derive(
        network="baseball",
        entry=entry,
        phases={"derive"},
        fresh_derive_flag=False,
        no_fresh_derive=True,
    )


@pytest.mark.smoke
def test_should_fresh_derive_non_baseball_false() -> None:
    entry = gr.load_networks_registry()["crm"]
    assert not gr.should_fresh_derive(
        network="crm",
        entry=entry,
        phases=None,
        fresh_derive_flag=True,
        no_fresh_derive=False,
    )


@pytest.mark.smoke
def test_should_fresh_derive_explicit_flag_without_registry() -> None:
    entry = gr.NetworkEntry(
        name="baseball",
        catalog_path=Path("catalogs/baseball.yaml"),
        anchors_path=None,
        default_root=Path("/tmp/baseball"),
        phases=["derive"],
        fresh_derive_before_gate=False,
    )
    assert gr.should_fresh_derive(
        network="baseball",
        entry=entry,
        phases={"derive"},
        fresh_derive_flag=True,
        no_fresh_derive=False,
    )


@pytest.mark.smoke
def test_networks_refresh_before_gate_flags() -> None:
    registry = gr.load_networks_registry()
    assert registry["empty-crm"].refresh_before_gate is True
    assert registry["crm-metering"].refresh_before_gate is True
    assert registry["crm"].refresh_before_gate is True
    assert registry["baseball"].refresh_before_gate is True


@pytest.mark.smoke
def test_load_catalog_baseball_has_minimum_scenarios() -> None:
    entry = gr.load_networks_registry()["baseball"]
    scenarios = gr.load_catalog(entry.catalog_path)
    assert len(scenarios) >= 34
    phases = {item.phase for item in scenarios}
    assert phases >= {
        "preflight",
        "identity",
        "m2",
        "pitching",
        "team_season",
        "fielding",
        "roster",
        "franchise",
        "derive",
        "bio_research",
        "infra",
    }


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
def test_resolve_template_anchor_list_whole_expr() -> None:
    anchors = {"nicknames": ["Hammer", "Hammerin' Hank"]}
    resolved = gr._resolve_template(
        "{{ anchors.nicknames }}",
        anchors=anchors,
        context={},
    )
    assert resolved == ["Hammer", "Hammerin' Hank"]


@pytest.mark.smoke
def test_check_assertions_path_one_of() -> None:
    public = {"results": [{"primary_nickname": "Hammerin' Hank"}]}
    failures = check_assertions(
        None,
        public=public,
        assertions={
            "path": {
                "results[0].primary_nickname": {
                    "one_of": ["Hammer", "Hammerin' Hank"],
                },
            },
        },
        context={},
    )
    assert failures == []
    failures = check_assertions(
        None,
        public={"results": [{"primary_nickname": "Henry"}]},
        assertions={
            "path": {
                "results[0].primary_nickname": {
                    "one_of": ["Hammer", "Hammerin' Hank"],
                },
            },
        },
        context={},
    )
    assert failures


@pytest.mark.smoke
def test_load_anchors_baseball_json() -> None:
    entry = gr.load_networks_registry()["baseball"]
    anchors = gr.load_anchors(entry.anchors_path)
    assert anchors["career_hr"] == 755
    assert anchors["career_avg"] == 0.305
    assert anchors["primary_nickname_accepted"] == ["Hammer", "Hammerin' Hank"]


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


@pytest.mark.smoke
def test_crm_metering_quote_scenario_attrs_on_step1() -> None:
    entry = gr.load_networks_registry()["crm-metering"]
    spec = next(
        item
        for item in gr.load_catalog(entry.catalog_path)
        if item.id == "meter-01-quote"
    )
    assert spec.step1.get("requested_attributes") == ["email"]
    assert spec.step2 is None
    assert spec.assert_step1.get("outcome") == "quote_required"


@pytest.mark.smoke
def test_missing_env_tavily_alias_uses_active_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEARCH_PROVIDER", "exa")
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    assert live_assertions.missing_env_vars(["TAVILY_API_KEY"]) == ["EXA_API_KEY"]
    monkeypatch.setenv("EXA_API_KEY", "exa-test")
    assert live_assertions.missing_env_vars(["TAVILY_API_KEY"]) == []

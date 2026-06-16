"""Smoke tests for baseball bootstrap experiment (heuristic path)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "examples" / "networks" / "baseball"))
import bootstrap_experiment as be  # noqa: E402


@pytest.fixture()
def lahman_fixture_dir(tmp_path: Path) -> Path:
    csv_dir = tmp_path / "lahman_csv"
    csv_dir.mkdir()
    (csv_dir / "Teams.csv").write_text(
        "yearID,lgID,teamID,franchID,name\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers\n"
        "1958,NL,LAN,LAD,Los Angeles Dodgers\n"
        "2024,NL,MIL,MIL,Milwaukee Brewers\n",
        encoding="utf-8",
    )
    (csv_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast\n"
        "1,aaronha01,Hank,Aaron\n",
        encoding="utf-8",
    )
    return csv_dir


def test_heuristic_bootstrap_commits_distinct_teams(lahman_fixture_dir: Path, tmp_path: Path) -> None:
    network_root = tmp_path / "baseball"
    report = be.run_bootstrap(
        seed=lahman_fixture_dir,
        network_root=network_root,
        use_llm=False,
    )
    assert report.teams_committed == 3
    assert report.distinct_raw_labels == 3
    registry_path = network_root / "bootstrap" / "team_registry.json"
    assert registry_path.is_file()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    names = {e["bind_values"]["team"] for e in registry["entities"].values()}
    assert names == {"Brooklyn Dodgers", "Los Angeles Dodgers", "Milwaukee Brewers"}
    assert registry["alias_index"]["brooklyn dodgers"]
"""Smoke tests for baseball franchise product specialist."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import refresh_baseball_root


@pytest.mark.smoke
def test_franchise_teams_includes_brooklyn_and_la(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    step1 = EntityQuery(
        lookup={"team": "Brooklyn Dodgers"},
        requested_attributes=["franchise_teams"],
        provenance=True,
    )
    r1 = run_query(step1, thread_id="franchise-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="franchise-step2",
    )
    assert r2.outcome in {"found", "assembled"}
    labels = json.loads(str(r2.results[0].get("franchise_teams")))
    assert "Brooklyn Dodgers" in labels
    assert "Los Angeles Dodgers" in labels
    version = r2.provenance["entities"][0]["attributes"]["franchise_teams"]["versions"][0]
    assert version.get("parameters", {}).get("lahman.teamID") == "BRO"
    assert version.get("parameters", {}).get("lahman.franchID") == "LAD"

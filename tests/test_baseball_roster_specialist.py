"""Smoke tests for baseball roster product specialist."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import refresh_baseball_root


@pytest.mark.smoke
def test_roster_scoped_1957_includes_aaron(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    step1 = EntityQuery(
        lookup={"team": "Brooklyn Dodgers"},
        scope={"yearID": "1957"},
        requested_attributes=["roster"],
        provenance=True,
    )
    r1 = run_query(step1, thread_id="roster-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="roster-step2",
    )
    assert r2.outcome in {"found", "assembled"}
    roster_raw = r2.results[0].get("roster")
    names = json.loads(str(roster_raw))
    assert "Hank Aaron" in names
    version = r2.provenance["entities"][0]["attributes"]["roster"]["versions"][0]
    assert version.get("parameters", {}).get("lahman.teamID") == "BRO"
    assert version.get("parameters", {}).get("yearID") == "1957"


@pytest.mark.smoke
def test_roster_without_scope_is_na(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    step1 = EntityQuery(
        lookup={"team": "Brooklyn Dodgers"},
        requested_attributes=["roster"],
    )
    r1 = run_query(step1, thread_id="roster-noscope-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="roster-noscope-step2",
    )
    assert r2.results
    assert r2.results[0].get("roster") == "N/A"


@pytest.mark.smoke
def test_roster_scoped_years_do_not_share_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    step1_1957 = EntityQuery(
        lookup={"team": "Brooklyn Dodgers"},
        scope={"yearID": "1957"},
        requested_attributes=["roster"],
    )
    r1 = run_query(step1_1957, thread_id="roster-1957-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="roster-1957-step2",
    )
    assert "Hank Aaron" in json.loads(str(r2.results[0].get("roster")))

    step1_1958 = EntityQuery(
        lookup={"team": "Brooklyn Dodgers"},
        scope={"yearID": "1958"},
        requested_attributes=["roster"],
    )
    r3 = run_query(step1_1958, thread_id="roster-1958-step1")
    assert r3.outcome == "lookup_resolved", r3.message
    r4 = run_query(
        EntityQuery(delivery_id=r3.delivery.delivery_id),
        thread_id="roster-1958-step2",
    )
    assert r4.results[0].get("roster") == "N/A"

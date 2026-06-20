"""Smoke tests for baseball team_season specialist warehouse reads."""

from __future__ import annotations

from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import refresh_baseball_root


def _deliver_season_wins(*, provenance: bool = False) -> tuple[object, object]:
    step1 = EntityQuery(
        lookup={"team": "Brooklyn Dodgers"},
        requested_attributes=["season_wins"],
        provenance=provenance,
    )
    r1 = run_query(step1, thread_id="season-wins-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    step2 = EntityQuery(delivery_id=r1.delivery.delivery_id)
    r2 = run_query(step2, thread_id="season-wins-step2")
    return r1, r2


@pytest.mark.smoke
def test_season_wins_latest_year(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_season_wins()
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert str(response.results[0].get("season_wins")) == "84"


@pytest.mark.smoke
def test_season_wins_provenance_team_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_season_wins(provenance=True)
    version = response.provenance["entities"][0]["attributes"]["season_wins"]["versions"][0]
    assert version.get("parameters", {}).get("lahman.teamID") == "BRO"


@pytest.mark.smoke
def test_season_wins_scoped_year(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    step1 = EntityQuery(
        lookup={"team": "Brooklyn Dodgers"},
        scope={"yearID": "1957"},
        requested_attributes=["season_wins", "season_losses"],
        provenance=True,
    )
    r1 = run_query(step1, thread_id="season-wins-scoped-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="season-wins-scoped-step2",
    )
    assert r2.outcome in {"found", "assembled"}
    assert str(r2.results[0].get("season_wins")) == "84"
    assert str(r2.results[0].get("season_losses")) == "70"
    version = r2.provenance["entities"][0]["attributes"]["season_wins"]["versions"][0]
    assert version.get("parameters", {}).get("yearID") == "1957"
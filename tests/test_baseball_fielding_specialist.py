"""Smoke tests for baseball fielding specialist warehouse compute."""

from __future__ import annotations

from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import SAMPLE_PLAYER, refresh_baseball_root


def _deliver_fielding(*, attrs: list[str], provenance: bool = False) -> tuple[object, object]:
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=attrs,
        provenance=provenance,
    )
    r1 = run_query(step1, thread_id="fielding-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="fielding-step2",
    )
    return r1, r2


@pytest.mark.smoke
def test_career_games_and_putouts_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_fielding(attrs=["career_games", "career_putouts"])
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert str(response.results[0].get("career_games")) == "15"
    assert str(response.results[0].get("career_putouts")) == "25"


@pytest.mark.smoke
def test_career_games_provenance_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_fielding(attrs=["career_games"], provenance=True)
    version = response.provenance["entities"][0]["attributes"]["career_games"]["versions"][0]
    assert version.get("computation", {}).get("inline")
    assert version.get("parameters", {}).get("lahman.playerID") == "aaronha01"
    assert version.get("parameters", {}).get("column") == "G"

"""Smoke tests for baseball pitching specialist warehouse compute."""

from __future__ import annotations

from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import SAMPLE_PLAYER, refresh_baseball_root


def _deliver_attr(
    attr: str,
    *,
    provenance: bool = False,
) -> tuple[object, object]:
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=[attr],
        provenance=provenance,
    )
    r1 = run_query(step1, thread_id=f"{attr}-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    step2 = EntityQuery(delivery_id=r1.delivery.delivery_id)
    r2 = run_query(step2, thread_id=f"{attr}-step2")
    return r1, r2


@pytest.mark.smoke
def test_career_wins_compute_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_attr("career_wins")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert str(response.results[0].get("career_wins")) == "5"


@pytest.mark.smoke
def test_career_wins_provenance_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_attr("career_wins", provenance=True)
    assert response.provenance
    version = response.provenance["entities"][0]["attributes"]["career_wins"]["versions"][0]
    assert version.get("computation", {}).get("inline")
    assert version.get("parameters", {}).get("lahman.playerID") == "aaronha01"
    assert version.get("parameters", {}).get("column") == "W"


@pytest.mark.smoke
def test_career_era_weighted_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_attr("career_era")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert response.results[0].get("career_era") == "3.000"


@pytest.mark.smoke
def test_career_era_provenance_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_attr("career_era", provenance=True)
    assert response.provenance
    version = response.provenance["entities"][0]["attributes"]["career_era"]["versions"][0]
    assert version.get("computation", {}).get("inline")
    assert version.get("parameters", {}).get("lahman.playerID") == "aaronha01"
    assert version.get("parameters", {}).get("attribute") == "career_era"
    inline = version.get("computation", {}).get("inline", "")
    assert "career_era_weighted" in inline or "IPouts" in inline

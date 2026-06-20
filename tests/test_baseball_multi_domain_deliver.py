"""Smoke tests for multi-specialist deliver across batting + pitching."""

from __future__ import annotations

from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import SAMPLE_PLAYER, refresh_baseball_root


@pytest.mark.smoke
def test_batting_and_pitching_same_deliver(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=["career_hr", "career_wins"],
        provenance=True,
    )
    r1 = run_query(step1, thread_id="multi-domain-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(EntityQuery(delivery_id=r1.delivery.delivery_id), thread_id="multi-domain-step2")
    assert r2.outcome in {"found", "assembled"}
    assert str(r2.results[0].get("career_hr")) == "3"
    assert str(r2.results[0].get("career_wins")) == "5"
    debug = r2.debug or ""
    assert "batting_specialist" in debug
    assert "pitching_specialist" in debug
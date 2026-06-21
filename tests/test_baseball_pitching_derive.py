"""Pitching-domain derive-on-miss smoke tests (mocked LLM)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import SAMPLE_PLAYER, refresh_baseball_root

WHIP_DERIVE_SOURCE = '''
def compute(player_id: str, warehouse: Path) -> str:
    rows = query_warehouse(
        warehouse,
        'SELECT COALESCE(SUM(CAST("BB" AS INTEGER)), 0), COALESCE(SUM(CAST("H" AS INTEGER)), 0), COALESCE(SUM(CAST("IPouts" AS INTEGER)), 0) FROM "Pitching" WHERE "playerID" = ?',
        (player_id,),
    )
    bb, h, ipouts = int(rows[0][0]), int(rows[0][1]), int(rows[0][2])
    if ipouts == 0:
        return "N/A"
    return f"{(bb + h) / (ipouts / 3.0):.3f}"
'''


def _load_derive_module(root: Path):
    live_loader = root / "specialists" / "specialist_loader.py"
    spec = importlib.util.spec_from_file_location("_pitch_derive_loader", live_loader)
    assert spec is not None and spec.loader is not None
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    return loader.load_derive_resolve()


def _patch_whip_derive(monkeypatch: pytest.MonkeyPatch, dr) -> None:
    def fake_invoke(prompt, *, llm_invoke=None):
        return WHIP_DERIVE_SOURCE.strip()

    def fake_review(prompt, *, review_llm_invoke=None):
        return "VERDICT: ACCEPT"

    monkeypatch.setattr(dr, "invoke_llm_for_prompt", fake_invoke)
    monkeypatch.setattr(dr, "invoke_llm_for_review", fake_review)


def _deliver(attr: str) -> object:
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=[attr],
    )
    r1 = run_query(step1, thread_id=f"{attr}-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    return run_query(EntityQuery(delivery_id=r1.delivery.delivery_id), thread_id=f"{attr}-step2")


@pytest.mark.smoke
def test_career_whip_derive_mocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = refresh_baseball_root(tmp_path, monkeypatch)
    dr = _load_derive_module(root)
    _patch_whip_derive(monkeypatch, dr)
    response = _deliver("career_whip")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert str(response.results[0].get("career_whip")) == "0.000"


@pytest.mark.smoke
def test_career_era_still_manifest_when_derive_on_miss_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    response = _deliver("career_era")
    assert response.results
    assert response.results[0].get("career_era") == "3.000"

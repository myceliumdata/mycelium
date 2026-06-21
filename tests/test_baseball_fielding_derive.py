"""Fielding-domain derive-on-miss smoke tests (mocked LLM)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import SAMPLE_PLAYER, refresh_baseball_root

FIELDING_PCT_SOURCE = '''
def compute(player_id: str, warehouse: Path) -> str:
    rows = query_warehouse(
        warehouse,
        'SELECT COALESCE(SUM(CAST("PO" AS INTEGER)), 0), COALESCE(SUM(CAST("A" AS INTEGER)), 0), COALESCE(SUM(CAST("E" AS INTEGER)), 0) FROM "Fielding" WHERE "playerID" = ?',
        (player_id,),
    )
    po, a, e = int(rows[0][0]), int(rows[0][1]), int(rows[0][2])
    denom = po + a + e
    if denom == 0:
        return "N/A"
    return f"{(po + a) / denom:.4f}"
'''


def _load_derive_module(root: Path):
    live_loader = root / "specialists" / "specialist_loader.py"
    spec = importlib.util.spec_from_file_location("_field_derive_loader", live_loader)
    assert spec is not None and spec.loader is not None
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    return loader.load_derive_resolve()


def _patch_fielding_derive(monkeypatch: pytest.MonkeyPatch, dr) -> None:
    monkeypatch.setattr(
        dr,
        "invoke_llm_for_prompt",
        lambda prompt, *, llm_invoke=None: FIELDING_PCT_SOURCE.strip(),
    )
    monkeypatch.setattr(
        dr,
        "invoke_llm_for_review",
        lambda prompt, *, review_llm_invoke=None: "VERDICT: ACCEPT",
    )


def _deliver() -> object:
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=["fielding_percentage"],
    )
    r1 = run_query(step1, thread_id="fielding-pct-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    return run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id="fielding-pct-step2",
    )


@pytest.mark.smoke
def test_fielding_percentage_derive_mocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = refresh_baseball_root(tmp_path, monkeypatch)
    dr = _load_derive_module(root)
    _patch_fielding_derive(monkeypatch, dr)
    response = _deliver()
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert str(response.results[0].get("fielding_percentage")) == "1.0000"

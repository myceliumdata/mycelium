"""Unit tests for derive warehouse context and semantic review parsing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from network.derive_sandbox import run_derive_function

REPO_ROOT = Path(__file__).resolve().parents[1]
DERIVE_PATH = REPO_ROOT / "examples/networks/baseball/specialists/derive_resolve.py"


def _load_derive_resolve():
    name = "derive_resolve_under_test"
    spec = importlib.util.spec_from_file_location(name, DERIVE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def dr():
    return _load_derive_resolve()


MINIMAL_MANIFEST = {
    "domains": {
        "batting": {
            "tables": ["Batting"],
            "grain": ["playerID", "yearID", "stint", "teamID", "lgID"],
            "conventions": {
                "career_sum": "SUM({column}) GROUP BY playerID",
                "rate_from_aggregates": "SUM operands then divide in Python",
            },
            "aliases": {
                "career_hr": {"convention": "career_sum", "column": "HR"},
            },
            "derive_candidates": ["career_avg"],
        },
    },
    "tables": {
        "Batting": {
            "columns": ["playerID", "H", "AB"],
            "row_count": 42,
        },
    },
}


def test_parse_review_verdict_accept(dr) -> None:
    verdict, reason = dr.parse_review_verdict("VERDICT: ACCEPT\n")
    assert verdict == "accept"
    assert reason == ""


def test_parse_review_verdict_reject(dr) -> None:
    verdict, reason = dr.parse_review_verdict(
        "VERDICT: REJECT\nREASON: Zero average implausible for non-zero hits.",
    )
    assert verdict == "reject"
    assert "implausible" in reason.lower()


def test_parse_review_verdict_unparseable_raises(dr) -> None:
    with pytest.raises(dr.DeriveReviewRejected, match="unparseable"):
        dr.parse_review_verdict("maybe accept?")


def test_format_warehouse_context_includes_grain_conventions_aliases(dr) -> None:
    text = dr.format_warehouse_context(MINIMAL_MANIFEST, "batting")
    assert "Grain: playerID, yearID, stint, teamID, lgID" in text
    assert "rate_from_aggregates" in text
    assert "career_hr: career_sum on column HR" in text
    assert "42 rows" in text
    assert "query_warehouse" in text
    assert "Integer aggregates stay integer" in text


def test_sql_int_div_fixture_returns_zero_on_minimal_rows(tmp_path: Path) -> None:
    from baseball_derive_fixtures import CAREER_AVG_DERIVE_SQL_INT_DIV_SOURCE

    db = tmp_path / "lahman.sqlite"
    import sqlite3

    conn = sqlite3.connect(db)
    conn.execute(
        'CREATE TABLE "Batting" ("playerID" TEXT, "H" INTEGER, "AB" INTEGER)',
    )
    conn.executemany(
        'INSERT INTO "Batting" VALUES (?, ?, ?)',
        [("aaronha01", 2, 4), ("aaronha01", 2, 4)],
    )
    conn.commit()
    conn.close()

    value = run_derive_function(
        CAREER_AVG_DERIVE_SQL_INT_DIV_SOURCE.strip(),
        player_id="aaronha01",
        warehouse=db,
    )
    assert value == "0.000"

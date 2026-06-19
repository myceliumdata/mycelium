"""Unit tests for derive sandbox validation and execution."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from network.derive_sandbox import DeriveSourceError, run_derive_function, validate_derive_source

CAREER_AVG_SOURCE = '''
def compute(player_id: str, warehouse: Path) -> str:
    rows = query_warehouse(
        warehouse,
        'SELECT COALESCE(SUM(CAST("H" AS INTEGER)), 0), COALESCE(SUM(CAST("AB" AS INTEGER)), 0) FROM "Batting" WHERE "playerID" = ?',
        (player_id,),
    )
    hits, ab = int(rows[0][0]), int(rows[0][1])
    if ab == 0:
        return "0.000"
    return f"{hits / ab:.3f}"
'''


def _make_batting_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        'CREATE TABLE "Batting" (playerID TEXT, H TEXT, AB TEXT)',
    )
    conn.execute(
        'INSERT INTO "Batting" VALUES ("a", "2", "4"), ("a", "2", "4")',
    )
    conn.commit()
    conn.close()


def test_validate_derive_source_rejects_import() -> None:
    with pytest.raises(DeriveSourceError, match="imports are not allowed"):
        validate_derive_source(
            "import os\n"
            "def compute(player_id, warehouse):\n"
            "    return '1'\n",
        )


def test_validate_derive_source_requires_compute() -> None:
    with pytest.raises(DeriveSourceError, match="compute"):
        validate_derive_source("def other():\n    return 1\n")


def test_run_derive_function_career_avg_example(tmp_path: Path) -> None:
    db = tmp_path / "lahman.sqlite"
    _make_batting_db(db)
    value = run_derive_function(
        CAREER_AVG_SOURCE,
        player_id="a",
        warehouse=db,
    )
    assert value == "0.500"

"""Shared fixtures for baseball derive codegen tests."""

from __future__ import annotations

# Minimal career_avg derive: SUM(H)/SUM(AB) on Batting — fixture Aaron → 0.500 (4 H, 8 AB).
CAREER_AVG_DERIVE_SOURCE = '''
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

# Invalid SQLite placeholder — triggers OperationalError on execution (retry guinea pig).
CAREER_AVG_DERIVE_BAD_SOURCE = '''
def compute(player_id: str, warehouse: Path) -> str:
    rows = query_warehouse(
        warehouse,
        'SELECT COALESCE(SUM(CAST("H" AS INTEGER)), 0), COALESCE(SUM(CAST("AB" AS INTEGER)), 0) FROM "Batting" WHERE "playerID" = %s',
        (player_id,),
    )
    hits, ab = int(rows[0][0]), int(rows[0][1])
    if ab == 0:
        return "0.000"
    return f"{hits / ab:.3f}"
'''

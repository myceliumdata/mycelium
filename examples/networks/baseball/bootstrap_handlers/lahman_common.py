"""Shared Lahman CSV ingest helpers for baseball bootstrap."""

from __future__ import annotations

import csv
import sqlite3
import zipfile
from pathlib import Path

BOOTSTRAP_TABLES = (
    "People",
    "Teams",
    "Appearances",
    "Batting",
    "Pitching",
    "Fielding",
    "TeamsFranchises",
)

LAHMAN_PLAYER_ID = "lahman.playerID"
LAHMAN_TEAM_ID = "lahman.teamID"


def resolve_network_seed(network_root: Path) -> Path | None:
    """Locate Lahman seed under ``<network_root>/seed/``."""
    seed_dir = network_root / "seed"
    if not seed_dir.is_dir():
        return None
    zip_path = seed_dir / "lahman_1871-2025_csv.zip"
    if zip_path.is_file():
        return zip_path
    nested = seed_dir / "lahman_1871-2025_csv"
    if nested.is_dir():
        return nested
    if any(seed_dir.glob("*.csv")):
        return seed_dir
    return None


def resolve_lahman_csv_dir(seed: Path) -> Path | None:
    """Resolve Lahman CSV directory from zip, nested folder, or flat CSV dir."""
    if not seed.exists():
        return None
    if seed.is_dir():
        nested = seed / "lahman_1871-2025_csv"
        if nested.is_dir():
            return nested
        if any(seed.glob("*.csv")):
            return seed
        return None
    if seed.suffix == ".zip" and seed.is_file():
        extract_to = seed.parent / "lahman_1871-2025_csv"
        if not extract_to.is_dir():
            extract_to.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(seed) as zf:
                zf.extractall(extract_to.parent)
        return extract_to
    return None


def _load_csv(conn: sqlite3.Connection, table: str, csv_path: Path) -> int:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return 0
        cols = [c.strip() for c in reader.fieldnames]
        safe_table = table.replace('"', '""')
        col_defs = ", ".join(f'"{c.replace(chr(34), chr(34) * 2)}" TEXT' for c in cols)
        conn.execute(f'DROP TABLE IF EXISTS "{safe_table}"')
        conn.execute(f'CREATE TABLE "{safe_table}" ({col_defs})')
        placeholders = ", ".join("?" for _ in cols)
        col_list = ", ".join(f'"{c.replace(chr(34), chr(34) * 2)}"' for c in cols)
        rows = 0
        batch: list[tuple[str, ...]] = []
        for row in reader:
            batch.append(tuple((row.get(c) or "").strip() for c in cols))
            if len(batch) >= 2000:
                conn.executemany(
                    f'INSERT INTO "{safe_table}" ({col_list}) VALUES ({placeholders})',
                    batch,
                )
                rows += len(batch)
                batch.clear()
        if batch:
            conn.executemany(
                f'INSERT INTO "{safe_table}" ({col_list}) VALUES ({placeholders})',
                batch,
            )
            rows += len(batch)
        conn.commit()
        return rows


def ingest_warehouse(csv_dir: Path, warehouse_path: Path) -> dict[str, int]:
    """Load bootstrap Lahman tables into ``warehouse/lahman.sqlite``."""
    warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    if warehouse_path.is_file():
        warehouse_path.unlink()
    conn = sqlite3.connect(warehouse_path)
    counts: dict[str, int] = {}
    try:
        for table in BOOTSTRAP_TABLES:
            path = csv_dir / f"{table}.csv"
            if path.is_file():
                counts[table] = _load_csv(conn, table, path)
    finally:
        conn.close()
    return counts


def distinct_team_label_rows(warehouse_path: Path) -> list[tuple[str, str, str]]:
    """Return stable ``(team_label, teamID, franchID)`` per distinct ``Teams.name``."""
    conn = sqlite3.connect(warehouse_path)
    try:
        rows = conn.execute(
            '''
            SELECT TRIM("name") AS label,
                   MIN(TRIM("teamID")) AS team_id,
                   MIN(TRIM("franchID")) AS franch_id
            FROM "Teams"
            WHERE TRIM(COALESCE("name", "")) != ""
            GROUP BY TRIM("name")
            ORDER BY label
            ''',
        ).fetchall()
        return [(str(label), str(team_id), str(franch_id)) for label, team_id, franch_id in rows]
    finally:
        conn.close()


def distinct_team_labels(warehouse_path: Path) -> list[str]:
    return [label for label, _, _ in distinct_team_label_rows(warehouse_path)]


def distinct_player_debut_rows(
    warehouse_path: Path,
) -> list[tuple[str, str, str, str]]:
    """Return stable ``(playerID, display_name, debut_year, debut_team)`` per player."""
    conn = sqlite3.connect(warehouse_path)
    try:
        try:
            conn.execute('SELECT 1 FROM "People" LIMIT 1')
        except sqlite3.OperationalError:
            return []
        rows = conn.execute(
            '''
            WITH player_display AS (
                SELECT
                    TRIM(p."playerID") AS player_id,
                    TRIM(p."nameFirst") || ' ' || TRIM(p."nameLast") AS display_name,
                    CASE
                        WHEN TRIM(COALESCE(p."debut", "")) != ""
                            THEN SUBSTR(TRIM(p."debut"), 1, 4)
                        ELSE (
                            SELECT CAST(MIN(CAST(a."yearID" AS INTEGER)) AS TEXT)
                            FROM "Appearances" a
                            WHERE a."playerID" = p."playerID"
                        )
                    END AS debut_year
                FROM "People" p
                WHERE TRIM(COALESCE(p."playerID", "")) != ""
                  AND TRIM(COALESCE(p."nameFirst", "")) != ""
                  AND TRIM(COALESCE(p."nameLast", "")) != ""
            )
            SELECT
                pd.player_id,
                pd.display_name,
                pd.debut_year,
                MIN(TRIM(t."name")) AS debut_team
            FROM player_display pd
            JOIN "Appearances" a
              ON a."playerID" = pd.player_id
             AND CAST(a."yearID" AS TEXT) = pd.debut_year
            JOIN "Teams" t
              ON t."yearID" = a."yearID"
             AND t."teamID" = a."teamID"
            WHERE TRIM(COALESCE(t."name", "")) != ""
              AND pd.debut_year IS NOT NULL
              AND TRIM(pd.debut_year) != ""
            GROUP BY pd.player_id, pd.display_name, pd.debut_year
            ORDER BY pd.player_id
            ''',
        ).fetchall()
        return [
            (str(player_id), str(name), str(year), str(team))
            for player_id, name, year, team in rows
        ]
    finally:
        conn.close()


def distinct_player_team_rows(warehouse_path: Path) -> list[tuple[str, str, str]]:
    """Return stable ``(playerID, display_name, team_label)`` rows from Appearances."""
    conn = sqlite3.connect(warehouse_path)
    try:
        try:
            conn.execute('SELECT 1 FROM "Appearances" LIMIT 1')
        except sqlite3.OperationalError:
            return []
        rows = conn.execute(
            '''
            SELECT DISTINCT
                p."playerID" AS player_id,
                TRIM(p."nameFirst") || ' ' || TRIM(p."nameLast") AS display_name,
                TRIM(t."name") AS team_label
            FROM "Appearances" a
            JOIN "People" p ON p."playerID" = a."playerID"
            JOIN "Teams" t ON t."yearID" = a."yearID" AND t."teamID" = a."teamID"
            WHERE TRIM(COALESCE(p."playerID", "")) != ""
              AND TRIM(COALESCE(p."nameFirst", "")) != ""
              AND TRIM(COALESCE(p."nameLast", "")) != ""
              AND TRIM(COALESCE(t."name", "")) != ""
            ORDER BY player_id, team_label, display_name
            ''',
        ).fetchall()
        return [(str(pid), str(name), str(team)) for pid, name, team in rows]
    finally:
        conn.close()

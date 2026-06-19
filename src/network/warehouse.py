"""Read-only warehouse access for pack specialists."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from network.paths import NetworkPaths


def default_warehouse_path(
    paths: NetworkPaths,
    *,
    relative: str = "warehouse/lahman.sqlite",
) -> Path:
    """Return the default warehouse sqlite path under a network root."""
    return paths.root / relative


def query_warehouse(path: Path, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    """Run a read-only query against a warehouse sqlite file."""
    if not path.is_file():
        msg = f"Warehouse database not found: {path}"
        raise FileNotFoundError(msg)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        cursor = conn.execute(sql, params)
        return list(cursor.fetchall())
    finally:
        conn.close()

"""SQLite path bootstrap for MCP health_check and process startup.

Identity lives in ``entities.json`` (``import_seed_file`` at bootstrap).
LangGraph checkpoints use ``checkpoints.sqlite`` separately.
``mycelium.db`` is optional; no identity tables are created.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class CoreStorage:
    """Ensure ``MYCELIUM_DB_PATH`` parent exists and open an empty SQLite file."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


_storage: CoreStorage | None = None


def get_storage(*, db_path: Path | None = None) -> CoreStorage:
    """Return process-wide storage singleton (DB path only; no seed import)."""
    global _storage
    if _storage is None:
        from network.paths import runtime_path

        resolved_db = db_path if db_path is not None else runtime_path("MYCELIUM_DB_PATH")
        _storage = CoreStorage(resolved_db)
    return _storage


def reset_storage() -> None:
    """Close and clear singleton (for tests)."""
    global _storage
    if _storage is not None:
        _storage.close()
        _storage = None

"""SQLite data layer for checkpoints and history in this phase.

People seeding moved to agents.seed (direct JSON). This module retained for
checkpoints/history only; the people table and seed_from_file remain for
compatibility but are no longer auto-populated on get_storage().

Schema: people(id, name, employer) only. Legacy DBs with extra columns are
documented in docs/database-notes.md.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from agents.seed import _assign_id
from models.state import SeedRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    employer TEXT
);

CREATE INDEX IF NOT EXISTS idx_people_name ON people(name);
"""


class CoreStorage:
    """Synchronous SQLite store for minimal core CRM people."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def seed_from_file(self, seed_path: Path) -> int:
        """Load seed CRM records; skip rows whose id already exists."""
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
        people = payload.get("people", [])
        inserted = 0
        for row in people:
            pid = row.get("id") or _assign_id(row)
            person = SeedRecord.model_validate(
                {
                    "id": pid,
                    "name": row["name"],
                    "employer": row.get("employer"),
                },
            )
            if self.upsert_person(person, on_conflict="ignore"):
                inserted += 1
        return inserted

    def upsert_person(self, person: SeedRecord, *, on_conflict: str = "replace") -> bool:
        """Insert or update a person. Returns False if ignored on conflict."""
        existing = self.get_person_by_id(person.id)
        if existing and on_conflict == "ignore":
            return False

        self._conn.execute(
            """
            INSERT INTO people (id, name, employer)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                employer = excluded.employer
            """,
            (person.id, person.name, person.employer),
        )
        self._conn.commit()
        return True

    def get_person_by_id(self, record_id: str) -> SeedRecord | None:
        row = self._conn.execute(
            "SELECT * FROM people WHERE id = ?",
            (record_id,),
        ).fetchone()
        return self._row_to_person(row) if row else None

    def find_persons(self, entity_key: str) -> list[SeedRecord]:
        """Resolve by id or exact name (case-insensitive).

        Id match returns zero or one person. Name match may return multiple records
        when the same name appears with different employers.
        """
        key = entity_key.strip()
        by_id = self.get_person_by_id(key)
        if by_id:
            return [by_id]

        rows = self._conn.execute(
            "SELECT * FROM people WHERE lower(name) = lower(?) ORDER BY id",
            (key,),
        ).fetchall()
        return [self._row_to_person(row) for row in rows]

    @staticmethod
    def _row_to_person(row: sqlite3.Row) -> SeedRecord:
        return SeedRecord(
            id=row["id"],
            name=row["name"],
            employer=row["employer"],
        )


_storage: CoreStorage | None = None


def get_storage(
    *,
    db_path: Path | None = None,
    seed_path: Path | None = None,
    auto_seed: bool = False,
) -> CoreStorage:
    """Return process-wide storage (no automatic CRM people seeding)."""
    global _storage
    if _storage is None:
        from network.paths import runtime_path

        resolved_db = db_path if db_path is not None else runtime_path("MYCELIUM_DB_PATH")
        _storage = CoreStorage(resolved_db)
        if auto_seed:
            resolved_seed = (
                seed_path if seed_path is not None else runtime_path("MYCELIUM_SEED_PATH")
            )
            if resolved_seed.exists():
                _storage.seed_from_file(resolved_seed)
    return _storage


def reset_storage() -> None:
    """Close and clear singleton (for tests)."""
    global _storage
    if _storage is not None:
        _storage.close()
        _storage = None

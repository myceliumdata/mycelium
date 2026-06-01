"""SQLite data layer for people, derivative datasets, and embedding stubs."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from models.state import DerivativeDatasetRef, Person

DEFAULT_DB_PATH = Path("data/mycelium.db")
DEFAULT_SEED_PATH = Path("data/seed_crm.json")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    employer TEXT,
    phone TEXT,
    title TEXT,
    extra_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS derivative_datasets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    attributes_json TEXT NOT NULL,
    agent_stub TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS derivative_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    data_json TEXT NOT NULL,
    FOREIGN KEY (dataset_id) REFERENCES derivative_datasets(id),
    FOREIGN KEY (person_id) REFERENCES people(id),
    UNIQUE (dataset_id, person_id)
);

CREATE TABLE IF NOT EXISTS person_embeddings (
    person_id TEXT PRIMARY KEY,
    embedding_json TEXT,
    FOREIGN KEY (person_id) REFERENCES people(id)
);

CREATE INDEX IF NOT EXISTS idx_people_email ON people(email);
CREATE INDEX IF NOT EXISTS idx_people_name ON people(name);
"""


class CoreStorage:
    """Synchronous SQLite store for core CRM and derivative dataset stubs."""

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
            person = Person.model_validate(row)
            if self.upsert_person(person, on_conflict="ignore"):
                inserted += 1
        return inserted

    def upsert_person(self, person: Person, *, on_conflict: str = "replace") -> bool:
        """Insert or update a person. Returns False if ignored on conflict."""
        existing = self.get_person_by_id(person.id)
        if existing and on_conflict == "ignore":
            return False

        self._conn.execute(
            """
            INSERT INTO people (id, name, email, employer, phone, title, extra_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                email = excluded.email,
                employer = excluded.employer,
                phone = excluded.phone,
                title = excluded.title,
                extra_json = excluded.extra_json
            """,
            (
                person.id,
                person.name,
                person.email,
                person.employer,
                person.phone,
                person.title,
                json.dumps(person.extra),
            ),
        )
        self._conn.commit()
        return True

    def get_person_by_id(self, person_id: str) -> Person | None:
        row = self._conn.execute(
            "SELECT * FROM people WHERE id = ?",
            (person_id,),
        ).fetchone()
        return self._row_to_person(row) if row else None

    def find_person(self, person_key: str) -> Person | None:
        """Resolve by id, email (case-insensitive), or exact name."""
        key = person_key.strip()
        by_id = self.get_person_by_id(key)
        if by_id:
            return by_id

        row = self._conn.execute(
            "SELECT * FROM people WHERE lower(email) = lower(?)",
            (key,),
        ).fetchone()
        if row:
            return self._row_to_person(row)

        row = self._conn.execute(
            "SELECT * FROM people WHERE lower(name) = lower(?)",
            (key,),
        ).fetchone()
        if row:
            return self._row_to_person(row)

        return None

    def list_derivative_attributes(self, person_id: str, dataset_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            """
            SELECT data_json FROM derivative_records
            WHERE person_id = ? AND dataset_id = ?
            """,
            (person_id, dataset_id),
        ).fetchone()
        if not row:
            return {}
        return json.loads(row["data_json"])

    def create_derivative_dataset(
        self,
        *,
        name: str,
        attributes: list[str],
        agent_stub: str = "derivative-agent-stub",
    ) -> DerivativeDatasetRef:
        dataset_id = f"ds-{uuid4().hex[:12]}"
        self._conn.execute(
            """
            INSERT INTO derivative_datasets (id, name, attributes_json, agent_stub, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (dataset_id, name, json.dumps(attributes), agent_stub, "pending"),
        )
        self._conn.commit()
        return DerivativeDatasetRef(
            dataset_id=dataset_id,
            name=name,
            attributes=attributes,
            status="pending",
            agent_stub=agent_stub,
        )

    def get_derivative_dataset(self, dataset_id: str) -> DerivativeDatasetRef | None:
        row = self._conn.execute(
            "SELECT * FROM derivative_datasets WHERE id = ?",
            (dataset_id,),
        ).fetchone()
        if not row:
            return None
        return DerivativeDatasetRef(
            dataset_id=row["id"],
            name=row["name"],
            attributes=json.loads(row["attributes_json"]),
            status=row["status"],
            agent_stub=row["agent_stub"],
        )

    def list_derivative_datasets(self) -> list[DerivativeDatasetRef]:
        rows = self._conn.execute(
            "SELECT * FROM derivative_datasets ORDER BY created_at DESC",
        ).fetchall()
        return [
            DerivativeDatasetRef(
                dataset_id=row["id"],
                name=row["name"],
                attributes=json.loads(row["attributes_json"]),
                status=row["status"],
                agent_stub=row["agent_stub"],
            )
            for row in rows
        ]

    def stub_activate_derivative(self, dataset_id: str) -> None:
        """Phase 1: mark dataset active without spawning a real agent."""
        self._conn.execute(
            "UPDATE derivative_datasets SET status = ? WHERE id = ?",
            ("stub_active", dataset_id),
        )
        self._conn.commit()

    def upsert_derivative_record(
        self,
        *,
        dataset_id: str,
        person_id: str,
        data: dict[str, Any],
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO derivative_records (dataset_id, person_id, data_json)
            VALUES (?, ?, ?)
            ON CONFLICT(dataset_id, person_id) DO UPDATE SET
                data_json = excluded.data_json
            """,
            (dataset_id, person_id, json.dumps(data)),
        )
        self._conn.commit()

    def store_embedding_stub(self, person_id: str, vector: list[float] | None = None) -> None:
        """Persist embedding JSON for future vector search (stub)."""
        self._conn.execute(
            """
            INSERT INTO person_embeddings (person_id, embedding_json)
            VALUES (?, ?)
            ON CONFLICT(person_id) DO UPDATE SET embedding_json = excluded.embedding_json
            """,
            (person_id, json.dumps(vector or [])),
        )
        self._conn.commit()

    def search_similar_stub(self, _query_vector: list[float], limit: int = 5) -> list[str]:
        """Phase 1: vector search not implemented; returns empty list."""
        _ = limit
        return []

    @staticmethod
    def _row_to_person(row: sqlite3.Row) -> Person:
        return Person(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            employer=row["employer"],
            phone=row["phone"],
            title=row["title"],
            extra=json.loads(row["extra_json"] or "{}"),
        )


_storage: CoreStorage | None = None


def get_storage(
    *,
    db_path: Path | None = None,
    seed_path: Path | None = None,
    auto_seed: bool = True,
) -> CoreStorage:
    """Return process-wide storage, seeding CRM data on first access."""
    global _storage
    if _storage is None:
        resolved_db = Path(os.getenv("MYCELIUM_DB_PATH", str(db_path or DEFAULT_DB_PATH)))
        _storage = CoreStorage(resolved_db)
        if auto_seed:
            resolved_seed = Path(
                os.getenv("MYCELIUM_SEED_PATH", str(seed_path or DEFAULT_SEED_PATH)),
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

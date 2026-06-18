"""SQLite minisql_v1 storage — shared by specialist and (future) entity stores."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS storage_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS entity_records (
    entity_id TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS field_records (
    entity_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    field_json TEXT NOT NULL,
    PRIMARY KEY (entity_id, field_name)
);
"""


def _connect(sqlite_path: Path) -> sqlite3.Connection:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)


def _touch_storage_meta(
    conn: sqlite3.Connection,
    *,
    version: str = "1.0",
    created_by: str | None = None,
) -> None:
    last_updated = datetime.now(timezone.utc).isoformat()
    by = created_by or "minisql_v1"
    conn.execute("DELETE FROM storage_meta")
    conn.execute(
        "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
        ("version", version),
    )
    conn.execute(
        "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
        ("last_updated", last_updated),
    )
    conn.execute(
        "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
        ("created_by", by),
    )


def _write_entity_fields(
    conn: sqlite3.Connection,
    entity_id: str,
    fields: dict[str, Any],
) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO entity_records (entity_id) VALUES (?)",
        (entity_id,),
    )
    if not isinstance(fields, dict):
        return
    for field_name, blob in fields.items():
        conn.execute(
            "INSERT OR REPLACE INTO field_records (entity_id, field_name, field_json) "
            "VALUES (?, ?, ?)",
            (entity_id, field_name, json.dumps(blob)),
        )


def _delete_entity(conn: sqlite3.Connection, entity_id: str) -> None:
    conn.execute("DELETE FROM field_records WHERE entity_id = ?", (entity_id,))
    conn.execute("DELETE FROM entity_records WHERE entity_id = ?", (entity_id,))


def _write_all_records(conn: sqlite3.Connection, records: dict[str, Any]) -> None:
    for entity_id, fields in records.items():
        if not isinstance(fields, dict):
            conn.execute(
                "INSERT OR REPLACE INTO entity_records (entity_id) VALUES (?)",
                (entity_id,),
            )
            continue
        conn.execute("DELETE FROM field_records WHERE entity_id = ?", (entity_id,))
        _write_entity_fields(conn, entity_id, fields)


def ensure_empty_sqlite(sqlite_path: Path) -> None:
    """Create an empty minisql_v1 database with schema."""
    conn = _connect(sqlite_path)
    try:
        _ensure_schema(conn)
        conn.execute("BEGIN")
        conn.execute("DELETE FROM field_records")
        conn.execute("DELETE FROM entity_records")
        conn.execute("DELETE FROM storage_meta")
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
            ("version", "1.0"),
        )
        conn.execute(
            "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
            ("last_updated", now),
        )
        conn.execute(
            "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
            ("created_by", "minisql_v1"),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_records(sqlite_path: Path) -> dict[str, Any]:
    """Return ``records`` dict keyed by entity id (versioned field blobs per field)."""
    return load_payload(sqlite_path).get("records", {})


def load_payload(sqlite_path: Path) -> dict[str, Any]:
    """Return full storage payload compatible with JSON ``storage.json`` shape."""
    if not sqlite_path.is_file():
        ensure_empty_sqlite(sqlite_path)
    conn = _connect(sqlite_path)
    try:
        _ensure_schema(conn)
        meta_rows = conn.execute("SELECT key, value FROM storage_meta").fetchall()
        meta_dict = {str(row["key"]): str(row["value"]) for row in meta_rows}
        records: dict[str, dict[str, Any]] = {}
        for row in conn.execute("SELECT entity_id FROM entity_records"):
            records[str(row["entity_id"])] = {}
        for row in conn.execute(
            "SELECT entity_id, field_name, field_json FROM field_records",
        ):
            entity_id = str(row["entity_id"])
            field_name = str(row["field_name"])
            records.setdefault(entity_id, {})[field_name] = json.loads(row["field_json"])
        return {
            "version": meta_dict.get("version", "1.0"),
            "last_updated": meta_dict.get("last_updated", ""),
            "records": records,
            "meta": {"created_by": meta_dict.get("created_by", "minisql_v1")},
        }
    finally:
        conn.close()


def load_entity_record(sqlite_path: Path, entity_id: str) -> dict[str, Any] | None:
    """Load one entity's versioned field blobs; ``None`` when the entity row is absent."""
    if not sqlite_path.is_file():
        return None
    conn = _connect(sqlite_path)
    try:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT 1 FROM entity_records WHERE entity_id = ?",
            (entity_id,),
        ).fetchone()
        if row is None:
            return None
        fields: dict[str, Any] = {}
        for field_row in conn.execute(
            "SELECT field_name, field_json FROM field_records WHERE entity_id = ?",
            (entity_id,),
        ):
            fields[str(field_row["field_name"])] = json.loads(field_row["field_json"])
        return fields
    finally:
        conn.close()


def upsert_entity_record(
    sqlite_path: Path,
    entity_id: str,
    fields: dict[str, Any],
    *,
    version: str = "1.0",
    created_by: str | None = None,
) -> None:
    """Upsert one entity's field rows and bump ``storage_meta.last_updated``."""
    if not sqlite_path.is_file():
        ensure_empty_sqlite(sqlite_path)
    conn = _connect(sqlite_path)
    try:
        _ensure_schema(conn)
        conn.execute("BEGIN")
        conn.execute("DELETE FROM field_records WHERE entity_id = ?", (entity_id,))
        if isinstance(fields, dict) and fields:
            _write_entity_fields(conn, entity_id, fields)
        elif not isinstance(fields, dict) or not fields:
            conn.execute(
                "INSERT OR REPLACE INTO entity_records (entity_id) VALUES (?)",
                (entity_id,),
            )
        _touch_storage_meta(conn, version=version, created_by=created_by)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_entity_record(sqlite_path: Path, entity_id: str) -> None:
    """Remove one entity and its field rows."""
    if not sqlite_path.is_file():
        return
    conn = _connect(sqlite_path)
    try:
        _ensure_schema(conn)
        conn.execute("BEGIN")
        _delete_entity(conn, entity_id)
        _touch_storage_meta(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_records(
    sqlite_path: Path,
    records: dict[str, Any],
    *,
    version: str = "1.0",
    created_by: str | None = None,
) -> None:
    """Persist ``records`` transactionally (replaces row set; no JSON file rewrite)."""
    payload: dict[str, Any] = {
        "version": version,
        "records": records,
        "meta": {"created_by": created_by or "minisql_v1"},
    }
    save_payload(sqlite_path, payload)


def save_payload(sqlite_path: Path, data: dict[str, Any]) -> None:
    """Persist full payload to SQLite in a single transaction."""
    if not sqlite_path.is_file():
        ensure_empty_sqlite(sqlite_path)
    records = data.get("records", {})
    if not isinstance(records, dict):
        records = {}
    last_updated = datetime.now(timezone.utc).isoformat()
    version = str(data.get("version", "1.0"))
    created_by = "minisql_v1"
    meta_block = data.get("meta")
    if isinstance(meta_block, dict) and meta_block.get("created_by"):
        created_by = str(meta_block["created_by"])

    conn = _connect(sqlite_path)
    try:
        _ensure_schema(conn)
        conn.execute("BEGIN")
        conn.execute("DELETE FROM field_records")
        conn.execute("DELETE FROM entity_records")
        _write_all_records(conn, records)
        conn.execute("DELETE FROM storage_meta")
        conn.execute(
            "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
            ("version", version),
        )
        conn.execute(
            "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
            ("last_updated", last_updated),
        )
        conn.execute(
            "INSERT INTO storage_meta (key, value) VALUES (?, ?)",
            ("created_by", created_by),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def migrate_versioned_provenance_v1_json(
    json_path: Path,
    sqlite_path: Path,
    *,
    category: str,
) -> None:
    """Copy versioned JSON storage into a new minisql_v1 SQLite file."""
    _ = category
    if json_path.is_file():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            payload = {"version": "1.0", "records": {}, "meta": {"created_by": "migration"}}
    else:
        payload = {
            "version": "1.0",
            "records": {},
            "meta": {"created_by": "migration"},
        }
    if "records" not in payload:
        payload["records"] = {}
    if "meta" not in payload or not isinstance(payload["meta"], dict):
        payload["meta"] = {"created_by": "migration"}
    save_payload(sqlite_path, payload)


_ENTITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS entity_storage_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS registry_entities (
    entity_id TEXT PRIMARY KEY,
    entity_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS registry_bind_index (
    bind_key TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL
);
"""


def _ensure_entity_sqlite(sqlite_path: Path) -> None:
    conn = _connect(sqlite_path)
    try:
        conn.executescript(_ENTITY_SCHEMA)
        conn.execute("BEGIN")
        conn.execute("DELETE FROM registry_entities")
        conn.execute("DELETE FROM registry_bind_index")
        conn.execute("DELETE FROM entity_storage_meta")
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO entity_storage_meta (key, value) VALUES (?, ?)",
            ("version", "1.0"),
        )
        conn.execute(
            "INSERT INTO entity_storage_meta (key, value) VALUES (?, ?)",
            ("last_updated", now),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_entities_document(sqlite_path: Path) -> dict[str, Any]:
    """Load entity registry document from minisql_v1 SQLite."""
    if not sqlite_path.is_file():
        _ensure_entity_sqlite(sqlite_path)
    conn = _connect(sqlite_path)
    try:
        meta_rows = conn.execute("SELECT key, value FROM entity_storage_meta").fetchall()
        meta_dict = {str(row["key"]): str(row["value"]) for row in meta_rows}
        entities: dict[str, Any] = {}
        for row in conn.execute("SELECT entity_id, entity_json FROM registry_entities"):
            entities[str(row["entity_id"])] = json.loads(row["entity_json"])
        bind_index: dict[str, str] = {}
        for row in conn.execute("SELECT bind_key, entity_id FROM registry_bind_index"):
            bind_index[str(row["bind_key"])] = str(row["entity_id"])
        return {
            "version": meta_dict.get("version", "1.0"),
            "last_updated": meta_dict.get("last_updated", ""),
            "entities": entities,
            "bind_index": bind_index,
        }
    finally:
        conn.close()


def save_entities_document(sqlite_path: Path, document: dict[str, Any]) -> None:
    """Persist entity registry document transactionally."""
    if not sqlite_path.is_file():
        _ensure_entity_sqlite(sqlite_path)
    entities = document.get("entities", {})
    bind_index = document.get("bind_index", {})
    if not isinstance(entities, dict):
        entities = {}
    if not isinstance(bind_index, dict):
        bind_index = {}
    last_updated = datetime.now(timezone.utc).isoformat()
    version = str(document.get("version", "1.0"))

    conn = _connect(sqlite_path)
    try:
        conn.executescript(_ENTITY_SCHEMA)
        conn.execute("BEGIN")
        conn.execute("DELETE FROM registry_entities")
        conn.execute("DELETE FROM registry_bind_index")
        for entity_id, entity_blob in entities.items():
            conn.execute(
                "INSERT INTO registry_entities (entity_id, entity_json) VALUES (?, ?)",
                (entity_id, json.dumps(entity_blob)),
            )
        for bind_key, entity_id in bind_index.items():
            conn.execute(
                "INSERT INTO registry_bind_index (bind_key, entity_id) VALUES (?, ?)",
                (bind_key, entity_id),
            )
        conn.execute("DELETE FROM entity_storage_meta")
        conn.execute(
            "INSERT INTO entity_storage_meta (key, value) VALUES (?, ?)",
            ("version", version),
        )
        conn.execute(
            "INSERT INTO entity_storage_meta (key, value) VALUES (?, ?)",
            ("last_updated", last_updated),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def migrate_entities_document_v1_json(
    json_path: Path,
    sqlite_path: Path,
    *,
    record_type: str,
) -> None:
    """Copy entities JSON document into minisql_v1 SQLite."""
    _ = record_type
    if json_path.is_file():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            payload = {
                "version": "1.0",
                "entities": {},
                "bind_index": {},
            }
    else:
        payload = {
            "version": "1.0",
            "entities": {},
            "bind_index": {},
        }
    if "entities" not in payload:
        payload["entities"] = {}
    if "bind_index" not in payload:
        payload["bind_index"] = {}
    save_entities_document(sqlite_path, payload)

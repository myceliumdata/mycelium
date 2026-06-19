"""Tests for incremental minisql_v1 per-entity specialist writes."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from agents.specialists.agent import SpecialistAgent, write_bind_fields_multi
from agents.specialists.base import SpecialistStorage
from agents.specialists.fields import current_value
from storage.minisql_v1 import (
    load_entity_record,
    load_payload,
    upsert_entity_record,
)
from versioned_storage_fixtures import versioned_found


@pytest.fixture
def agent_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    agents_dir = tmp_path / "agent_data"
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(agents_dir))
    return agents_dir


def _seed_minisql(storage: SpecialistStorage) -> None:
    storage.save(
        {
            "version": "1.0",
            "records": {
                "entity-a": {
                    "name": versioned_found(
                        at="2026-06-17T10:00:00+00:00",
                        value="Alice",
                    ),
                },
                "entity-b": {
                    "email": versioned_found(
                        at="2026-06-17T10:00:00+00:00",
                        value="b@example.com",
                    ),
                },
            },
            "meta": {"created_by": "test"},
        },
    )
    storage.migrate_to("minisql_v1")


def _field_json_snapshot(sqlite_path: Path, entity_id: str) -> dict[str, str]:
    conn = sqlite3.connect(str(sqlite_path))
    try:
        rows = conn.execute(
            "SELECT field_name, field_json FROM field_records WHERE entity_id = ?",
            (entity_id,),
        ).fetchall()
        return {name: blob for name, blob in rows}
    finally:
        conn.close()


@pytest.mark.smoke
def test_incremental_write_preserves_unrelated_entities(agent_data_dir: Path) -> None:
    storage = SpecialistStorage(category="demographic", base_dir=agent_data_dir)
    _seed_minisql(storage)
    before_a = _field_json_snapshot(storage.sqlite_file, "entity-a")
    before_b = _field_json_snapshot(storage.sqlite_file, "entity-b")

    agent = SpecialistAgent(category="demographic", agent_name="demographic_specialist")
    agent.write_fields(
        "entity-c",
        {"name": "Charlie"},
        actor_kind="bind",
        at="2026-06-17T12:00:00+00:00",
    )

    assert _field_json_snapshot(storage.sqlite_file, "entity-a") == before_a
    assert _field_json_snapshot(storage.sqlite_file, "entity-b") == before_b
    loaded_c = load_entity_record(storage.sqlite_file, "entity-c")
    assert loaded_c is not None
    assert current_value(loaded_c["name"]) == "Charlie"


@pytest.mark.smoke
def test_incremental_save_skips_table_wide_delete(
    agent_data_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = SpecialistStorage(category="contact", base_dir=agent_data_dir)
    _seed_minisql(storage)
    executed: list[str] = []

    import storage.minisql_v1 as minisql_mod

    original_connect = minisql_mod._connect

    def tracing_connect(sqlite_path: Path) -> sqlite3.Connection:
        conn = original_connect(sqlite_path)
        conn.set_trace_callback(lambda sql: executed.append(sql.strip()))
        return conn

    monkeypatch.setattr(minisql_mod, "_connect", tracing_connect)
    upsert_entity_record(
        storage.sqlite_file,
        "entity-a",
        {
            "name": versioned_found(
                at="2026-06-17T13:00:00+00:00",
                value="Alice Updated",
            ),
        },
    )

    assert not any(
        stmt.upper() == "DELETE FROM FIELD_RECORDS" for stmt in executed
    )
    assert not any(
        stmt.upper() == "DELETE FROM ENTITY_RECORDS" for stmt in executed
    )


@pytest.mark.smoke
def test_write_na_field_uses_incremental_save_entity(agent_data_dir: Path) -> None:
    storage = SpecialistStorage(category="batting", base_dir=agent_data_dir)
    _seed_minisql(storage)
    before_a = _field_json_snapshot(storage.sqlite_file, "entity-a")

    agent = SpecialistAgent(category="batting", agent_name="batting_specialist")
    agent.write_na_field(
        "entity-c",
        "career_hr",
        at="2026-06-17T12:00:00+00:00",
    )

    assert _field_json_snapshot(storage.sqlite_file, "entity-a") == before_a
    loaded_c = load_entity_record(storage.sqlite_file, "entity-c")
    assert loaded_c is not None
    assert current_value(loaded_c.get("career_hr")) is None
    from agents.specialists.fields import current_status

    assert current_status(loaded_c["career_hr"]) == "na"


@pytest.mark.smoke
def test_write_bind_fields_multi_rollback_per_entity(
    agent_data_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    demographic = SpecialistStorage(category="demographic", base_dir=agent_data_dir)
    professional = SpecialistStorage(category="professional", base_dir=agent_data_dir)
    _seed_minisql(demographic)
    _seed_minisql(professional)

    entity_id = "rollback-entity"
    demographic.save_entity(
        entity_id,
        {
            "name": versioned_found(
                at="2026-06-17T10:00:00+00:00",
                value="Rollback Person",
            ),
        },
    )
    professional.save_entity(
        entity_id,
        {
            "employer": versioned_found(
                at="2026-06-17T10:00:00+00:00",
                value="First Co",
            ),
        },
    )

    before_demo = load_entity_record(demographic.sqlite_file, entity_id)
    before_prof = load_entity_record(professional.sqlite_file, entity_id)
    unrelated_before = load_entity_record(demographic.sqlite_file, "entity-a")

    original_upsert = upsert_entity_record
    calls = {"count": 0}

    def flaky_upsert(
        sqlite_path: Path,
        entity_id_arg: str,
        fields: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated upsert failure")
        original_upsert(sqlite_path, entity_id_arg, fields, **kwargs)

    monkeypatch.setattr(
        "storage.minisql_v1.upsert_entity_record",
        flaky_upsert,
    )

    def resolve_owner(field: str) -> tuple[str, str]:
        if field == "name":
            return ("demographic", "demographic_specialist")
        if field == "employer":
            return ("professional", "professional_specialist")
        raise KeyError(field)

    with pytest.raises(OSError, match="simulated upsert failure"):
        write_bind_fields_multi(
            entity_id,
            {"name": "Rollback Person", "employer": "New Co"},
            resolve_owner=resolve_owner,
            actor_kind="bind",
            at="2026-06-17T14:00:00+00:00",
        )

    after_demo = load_entity_record(demographic.sqlite_file, entity_id)
    after_prof = load_entity_record(professional.sqlite_file, entity_id)
    unrelated_after = load_entity_record(demographic.sqlite_file, "entity-a")

    assert after_demo == before_demo
    assert after_prof == before_prof
    assert unrelated_after == unrelated_before


@pytest.mark.smoke
def test_bulk_save_payload_still_roundtrips(agent_data_dir: Path) -> None:
    storage = SpecialistStorage(category="social", base_dir=agent_data_dir)
    _seed_minisql(storage)
    payload = load_payload(storage.sqlite_file)
    payload["records"]["entity-d"] = {
        "twitter": versioned_found(
            at="2026-06-17T15:00:00+00:00",
            value="@delta",
        ),
    }
    storage.save(payload)
    loaded = storage.load()
    assert current_value(loaded["records"]["entity-d"]["twitter"]) == "@delta"
    assert len(loaded["records"]) == 3

"""Tests for minisql_v1 specialist storage migration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.specialists.agent import SpecialistAgent
from agents.specialists.base import SpecialistStorage
from agents.specialists.fields import current_value, is_versioned_field
from storage.minisql_v1 import load_payload, migrate_versioned_provenance_v1_json
from versioned_storage_fixtures import versioned_found


@pytest.fixture
def agent_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    agents_dir = tmp_path / "agent_data"
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(agents_dir))
    return agents_dir


@pytest.mark.smoke
def test_minisql_v1_migrates_json_backup(agent_data_dir: Path) -> None:
    storage = SpecialistStorage(category="contact", base_dir=agent_data_dir)
    entity_id = "entity-backup-test"
    storage.save(
        {
            "version": "1.0",
            "records": {
                entity_id: {
                    "email": versioned_found(
                        at="2026-06-17T10:00:00+00:00",
                        value="a@example.com",
                    ),
                },
            },
            "meta": {"created_by": "test"},
        },
    )
    storage.migrate_to("minisql_v1")

    assert storage.current_strategy() == "minisql_v1"
    assert not storage.storage_file.exists()
    assert (storage.base_dir / "storage.json.pre-minisql-v1").is_file()
    assert storage.sqlite_file.is_file()
    strategy = storage.get_strategy()
    assert strategy["last_migrated"] is not None
    assert "upgrade_path" in strategy


@pytest.mark.smoke
def test_minisql_v1_read_write_roundtrip(agent_data_dir: Path) -> None:
    storage = SpecialistStorage(category="demographic", base_dir=agent_data_dir)
    entity_id = "entity-roundtrip"
    storage.save(
        {
            "version": "1.0",
            "records": {
                entity_id: {
                    "name": versioned_found(
                        at="2026-06-17T11:00:00+00:00",
                        value="Paul Murphy",
                        category="demographic",
                        specialist_name="demographic_specialist",
                    ),
                },
            },
            "meta": {"created_by": "test"},
        },
    )
    storage.migrate_to("minisql_v1")

    loaded = storage.load()
    name_entry = loaded["records"][entity_id]["name"]
    assert is_versioned_field(name_entry)
    assert current_value(name_entry) == "Paul Murphy"

    storage.save(loaded)
    after_write = storage.load()
    name_entry = after_write["records"][entity_id]["name"]
    assert current_value(name_entry) == "Paul Murphy"
    assert is_versioned_field(name_entry)
    assert len(name_entry.get("versions", [])) >= 1


@pytest.mark.smoke
def test_minisql_v1_shared_module_migrate(agent_data_dir: Path) -> None:
    json_path = agent_data_dir / "social" / "storage.json"
    sqlite_path = agent_data_dir / "social" / "storage.sqlite"
    json_path.parent.mkdir(parents=True)
    json_path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "records": {
                    "e1": {
                        "twitter": versioned_found(
                            at="2026-06-17T12:00:00+00:00",
                            value="@handle",
                            category="social",
                            specialist_name="social_specialist",
                        ),
                    },
                },
                "meta": {"created_by": "fixture"},
            },
        ),
        encoding="utf-8",
    )
    migrate_versioned_provenance_v1_json(json_path, sqlite_path, category="social")
    payload = load_payload(sqlite_path)
    assert current_value(payload["records"]["e1"]["twitter"]) == "@handle"


@pytest.mark.smoke
def test_optimize_storage_triggers_migration(
    agent_data_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD", "2")
    agent = SpecialistAgent(category="professional", agent_name="professional_specialist")
    agent.storage.save(
        {
            "version": "1.0",
            "records": {
                "existing-one": {},
                "existing-two": {},
            },
            "meta": {"created_by": "test"},
        },
    )
    assert agent.storage.current_strategy() == "versioned_provenance_v1"

    result = agent.write_fields(
        "new-entity",
        {"employer": "Acme Corp"},
        actor_kind="bind",
    )

    assert agent.storage.current_strategy() == "minisql_v1"
    assert (agent.storage.base_dir / "storage.json.pre-minisql-v1").is_file()
    assert result == {"employer": "Acme Corp"}
    loaded = agent.storage.load()
    assert loaded["records"]["new-entity"]["employer"]["versions"][0]["value"] == "Acme Corp"


@pytest.mark.smoke
def test_minisql_v1_idempotent_migrate(agent_data_dir: Path) -> None:
    storage = SpecialistStorage(category="contact", base_dir=agent_data_dir)
    storage.migrate_to("minisql_v1")
    storage.migrate_to("minisql_v1")
    assert storage.current_strategy() == "minisql_v1"


@pytest.mark.smoke
def test_minisql_v1_synthetic_records_migration_completes(agent_data_dir: Path) -> None:
    storage = SpecialistStorage(category="demographic", base_dir=agent_data_dir)
    records = {f"entity-{i}": {} for i in range(60)}
    storage.save({"version": "1.0", "records": records, "meta": {"created_by": "test"}})
    storage.migrate_to("minisql_v1")
    loaded = storage.load()
    assert len(loaded["records"]) == 60

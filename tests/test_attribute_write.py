"""Smoke tests: Program 2 Slice 1 — unified MVR bind-field writes."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typing import Any

import pytest

from agents.attribute_write import (
    ensure_entity_bind,
    ensure_entity_bind_fields,
    resolve_attribute_owner,
    write_bind_fields,
)
from agents.classification import get_category_tree, reset_category_tree
from agents.entity_registry import get_entity_registry, make_bind_key, reset_entity_registry
from agents.specialist_fields import current_value, is_versioned_field
from agents.specialists.base import SpecialistStorage
from agents.target_deliver import bind_provisional_from_scope
from graphs.core import reset_core_graph
from network.delivery import DeliveryScope
from network.mvr import load_mvr
from network_helpers import import_seed_for_test
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def attribute_write_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_category_tree()

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")

    reset_category_tree()
    get_category_tree()
    storage = get_storage()
    return storage


def _specialist_field(entity_id: str, category: str, field: str) -> dict | None:
    storage = SpecialistStorage(category)
    data = storage.load()
    record = (data.get("records") or {}).get(entity_id) or {}
    entry = record.get(field)
    return entry if isinstance(entry, dict) else None


@pytest.mark.smoke
def test_resolve_attribute_owner_maps_mvr_fields(attribute_write_env: CoreStorage) -> None:
    _ = attribute_write_env
    assert resolve_attribute_owner("name") == ("demographic", "demographic_specialist")
    assert resolve_attribute_owner("employer") == (
        "professional",
        "professional_specialist",
    )


@pytest.mark.smoke
def test_bind_creates_specialist_versions_and_cache(attribute_write_env: CoreStorage) -> None:
    _ = attribute_write_env
    registry = get_entity_registry()
    entity, created = ensure_entity_bind(
        "Road Runner",
        "Acme Corp",
        source="query_bind",
        validation_state="provisional",
    )
    assert created is False
    assert entity.name == "Road Runner"
    assert entity.employer == "Acme Corp"
    assert entity.attr_sources["name"] == "demographic"
    assert entity.attr_sources["employer"] == "professional"

    name_entry = _specialist_field(entity.id, "demographic", "name")
    employer_entry = _specialist_field(entity.id, "professional", "employer")
    assert name_entry is not None and is_versioned_field(name_entry)
    assert employer_entry is not None and is_versioned_field(employer_entry)
    assert current_value(name_entry) == "Road Runner"
    assert current_value(employer_entry) == "Acme Corp"

    assert registry.lookup_by_bind_key("Road Runner", "Acme Corp") is not None
    indexes = registry.field_indexes()
    assert entity.id in indexes["name"].get("road runner", [])
    assert entity.id in indexes["employer"].get("acme corp", [])


@pytest.mark.smoke
def test_replace_employer_updates_indexes(attribute_write_env: CoreStorage) -> None:
    _ = attribute_write_env
    registry = get_entity_registry()
    entity, _ = ensure_entity_bind(
        "Pat Example",
        "Old Co",
        source="query_bind",
        validation_state="validated",
    )
    old_key = make_bind_key("Pat Example", "Old Co")
    assert registry._data.bind_index.get(old_key) == entity.id

    write_bind_fields(
        entity.id,
        {"name": "Pat Example", "employer": "New Co"},
        actor_kind="bind",
    )
    new_key = make_bind_key("Pat Example", "New Co")
    assert old_key not in registry._data.bind_index
    assert registry._data.bind_index.get(new_key) == entity.id
    assert registry.lookup_by_bind_key("Pat Example", "New Co") is not None
    assert registry.lookup_by_bind_key("Pat Example", "Old Co") is None


@pytest.mark.smoke
def test_unmapped_mvr_field_raises(attribute_write_env: CoreStorage) -> None:
    _ = attribute_write_env
    import os

    network_path = Path(os.environ["MYCELIUM_NETWORK_ROOT"]) / "network.json"
    data = json.loads(network_path.read_text(encoding="utf-8"))
    data["mvr"] = {
        "bind_fields": ["name", "employer", "nickname"],
        "description": "test",
    }
    network_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="attribute_map"):
        ensure_entity_bind_fields(
            {"name": "A", "employer": "B", "nickname": "n"},
            source="query_bind",
            validation_state="provisional",
        )


@pytest.mark.smoke
def test_import_seed_writes_specialist_versions(attribute_write_env: CoreStorage) -> None:
    _ = attribute_write_env
    import os

    seed_path = Path(os.environ["MYCELIUM_SEED_PATH"])
    count = import_seed_for_test(seed_path)
    assert count > 0

    registry = get_entity_registry()
    entity = registry.lookup_by_bind_key("Andrea Kalmans", "Lontra Ventures")
    assert entity is not None

    name_entry = _specialist_field(entity.id, "demographic", "name")
    employer_entry = _specialist_field(entity.id, "professional", "employer")
    assert name_entry is not None and current_value(name_entry) == "Andrea Kalmans"
    assert employer_entry is not None and current_value(employer_entry) == "Lontra Ventures"
    assert (name_entry.get("versions") or [{}])[0]["actor"]["kind"] == "seed_bootstrap"


@pytest.mark.smoke
def test_bind_provisional_from_scope_uses_unified_write(
    attribute_write_env: CoreStorage,
) -> None:
    _ = attribute_write_env
    scope = DeliveryScope(
        delivery_id="d_test",
        expires_at="2026-06-13T12:00:00+00:00",
        lookup={"name": "Scope Person", "employer": "Scope Inc"},
        create_on_deliver=True,
    )
    entity = bind_provisional_from_scope(scope)
    assert entity.name == "Scope Person"
    assert entity.employer == "Scope Inc"

    name_entry = _specialist_field(entity.id, "demographic", "name")
    assert name_entry is not None
    assert (name_entry.get("versions") or [{}])[0]["actor"]["kind"] == "bind"


@pytest.mark.smoke
def test_write_bind_fields_skips_duplicate_version(
    attribute_write_env: CoreStorage,
) -> None:
    _ = attribute_write_env
    entity, _ = ensure_entity_bind(
        "No Op Person",
        "Stable Co",
        source="query_bind",
        validation_state="validated",
    )
    write_bind_fields(
        entity.id,
        {"name": "No Op Person", "employer": "Stable Co"},
        actor_kind="bind",
    )
    name_entry = _specialist_field(entity.id, "demographic", "name")
    assert name_entry is not None
    assert len(name_entry.get("versions") or []) == 1


@pytest.mark.smoke
def test_write_bind_fields_rollback_on_second_save_failure(
    attribute_write_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = attribute_write_env
    entity, _ = ensure_entity_bind(
        "Rollback Person",
        "First Co",
        source="query_bind",
        validation_state="validated",
    )
    demographic = SpecialistStorage("demographic")
    before = demographic.load()

    original_save = SpecialistStorage.save
    calls = {"count": 0}

    def flaky_save(self: SpecialistStorage, data: dict[str, Any]) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated save failure")
        original_save(self, data)

    monkeypatch.setattr(SpecialistStorage, "save", flaky_save)

    with pytest.raises(OSError, match="simulated save failure"):
        write_bind_fields(
            entity.id,
            {"name": "Rollback Person", "employer": "New Co"},
            actor_kind="bind",
        )

    after = demographic.load()
    assert after.get("records") == before.get("records")


@pytest.mark.smoke
def test_bind_provisional_from_scope_collects_all_mvr_bind_fields(
    attribute_write_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = attribute_write_env
    import os

    network_path = Path(os.environ["MYCELIUM_NETWORK_ROOT"]) / "network.json"
    data = json.loads(network_path.read_text(encoding="utf-8"))
    data["mvr"] = {
        "bind_fields": ["name", "employer", "account_id"],
        "description": "test",
    }
    network_path.write_text(json.dumps(data), encoding="utf-8")

    categories_path = Path(os.environ["MYCELIUM_CATEGORIES_PATH"])
    categories = json.loads(categories_path.read_text(encoding="utf-8"))
    categories["attribute_map"]["account_id"] = "contact"
    categories["categories"]["contact"]["examples"].append("account_id")
    categories_path.write_text(json.dumps(categories), encoding="utf-8")
    reset_category_tree()
    get_category_tree()

    scope = DeliveryScope(
        delivery_id="d_custom",
        expires_at="2026-06-13T12:00:00+00:00",
        lookup={
            "name": "Acct Person",
            "employer": "Acct Co",
            "account_id": "ACME-99",
        },
        create_on_deliver=True,
    )
    entity = bind_provisional_from_scope(scope)
    assert entity.name == "Acct Person"
    assert entity.employer == "Acct Co"

    account_entry = _specialist_field(entity.id, "contact", "account_id")
    assert account_entry is not None
    assert current_value(account_entry) == "ACME-99"


@pytest.mark.smoke
def test_mvr_policy_lists_mapped_bind_fields(attribute_write_env: CoreStorage) -> None:
    _ = attribute_write_env
    policy = load_mvr()
    for field in policy.bind_fields:
        resolve_attribute_owner(field)

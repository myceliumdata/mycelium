"""Tests for SpecialistAgent class and protocol instance routing."""

from __future__ import annotations

import importlib
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.entity_registry import reset_entity_registry
from agents.registry import get_agent_registry, reset_agent_registry
from agents.specialists.agent import SpecialistAgent
from agents.specialists.protocol import dispatch_write_bind_fields_multi, dispatch_write_fields
from graphs.core import reset_core_graph
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture(autouse=True)
def _isolate_agent_registry() -> None:
    reset_agent_registry()
    yield
    reset_agent_registry()


@pytest.fixture
def attribute_write_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()

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
    return get_storage()


class CountingSpecialist(SpecialistAgent):
    category = "professional"
    agent_name = "professional_specialist"

    def __init__(self) -> None:
        super().__init__(category="professional", agent_name="professional_specialist")
        self.writes = 0

    def write_fields(
        self,
        entity_id: str,
        fields: dict[str, str],
        *,
        actor_kind: str,
        at: str | None = None,
    ) -> dict[str, str]:
        self.writes += 1
        return super().write_fields(
            entity_id,
            fields,
            actor_kind=actor_kind,
            at=at,
        )


class MigratingSpecialist(SpecialistAgent):
    category = "contact"
    agent_name = "contact_specialist"

    def __init__(self) -> None:
        super().__init__(category="contact", agent_name="contact_specialist")
        self.migrated = False

    def optimize_storage(self) -> bool:
        return True

    def migrate_to(self, target: str) -> None:
        if target == "minisql_v1":
            self.migrated = True


@pytest.mark.smoke
def test_registry_resolves_agent_singleton(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    reset_agent_registry()
    agent = get_agent_registry().get_agent_instance("demographic_specialist")
    assert agent is not None
    assert agent.category == "demographic"
    assert agent.agent_name == "demographic_specialist"


@pytest.mark.smoke
def test_dispatch_write_fields_uses_subclass_override(
    attribute_write_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = attribute_write_env
    professional_mod = importlib.import_module("agents.specialists.professional_specialist")
    counting = CountingSpecialist()
    monkeypatch.setattr(professional_mod, "AGENT", counting)
    dispatch_write_fields(
        "professional_specialist",
        "entity-counting-test",
        {"employer": "Acme Corp"},
        actor_kind="bind",
    )
    assert counting.writes == 1


@pytest.mark.smoke
def test_optimize_storage_hook_before_write(attribute_write_env: CoreStorage) -> None:
    _ = attribute_write_env
    migrating = MigratingSpecialist()
    migrating.write_fields(
        "entity-migrate-test",
        {"email": "a@example.com"},
        actor_kind="bind",
    )
    assert migrating.migrated


@pytest.mark.smoke
@patch("agents.specialists.handlers.write_fields")
def test_write_bind_fields_multi_routes_through_agent(
    handlers_write_mock: object,
    attribute_write_env: CoreStorage,
) -> None:
    _ = attribute_write_env
    dispatch_write_bind_fields_multi(
        "entity-multi-test",
        {"name": "Paul Murphy", "employer": "Acme Corp"},
        actor_kind="bind",
        at="2026-06-17T12:00:00+00:00",
    )
    handlers_write_mock.assert_not_called()


@pytest.mark.smoke
def test_write_bind_fields_multi_uses_subclass_override(
    attribute_write_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = attribute_write_env
    professional_mod = importlib.import_module("agents.specialists.professional_specialist")
    counting = CountingSpecialist()
    monkeypatch.setattr(professional_mod, "AGENT", counting)
    dispatch_write_bind_fields_multi(
        "entity-multi-counting-test",
        {"name": "Paul Murphy", "employer": "Acme Corp"},
        actor_kind="bind",
        at="2026-06-17T12:00:00+00:00",
    )
    assert counting.writes == 1

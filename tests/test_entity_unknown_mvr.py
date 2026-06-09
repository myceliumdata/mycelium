"""Smoke tests for entity_unknown + MVR policy (entity protocol slice 3)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import reset_entity_registry
from agents.entity_resolution import resolve_entity_key
from agents.seed import get_seed_data, reset_seed_data
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.introspection import build_network_capabilities
from network.mvr import load_mvr
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


def _write_network_root_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")


@pytest.fixture
def crm_mvr_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """Isolated CRM network with committed MVR policy."""
    reset_storage()
    reset_seed_data()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()

    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    _write_network_root_env(tmp_path, monkeypatch)

    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_category_tree()
    from agents.classification import get_category_tree

    get_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    storage = get_storage()
    storage.seed_from_file(seed)
    reset_seed_data()
    _ = get_seed_data()

    yield storage

    reset_storage()
    reset_seed_data()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_load_mvr_from_network_json(crm_mvr_env: CoreStorage) -> None:
    _ = crm_mvr_env
    policy = load_mvr()
    assert policy.bind_fields == ["name", "employer"]
    assert policy.name_source == "entity_key"
    assert policy.required_fields_for_entity_key("Paul Murphy") == ["employer"]


@pytest.mark.smoke
def test_paul_murphy_email_entity_unknown_no_specialists(
    crm_mvr_env: CoreStorage,
) -> None:
    response = run_query(
        EntityQuery(entity_key="Paul Murphy", requested_attributes=["email"]),
    )

    assert response.outcome == "entity_unknown"
    assert response.required_fields == ["employer"]
    assert response.results == []
    assert response.suggestions == []
    assert "employer" in response.message.lower()
    assert "email" in response.message.lower()
    assert "classified" not in response.debug.lower()
    assert "invoke_specialists" not in response.debug
    assert "outcome='entity_unknown'" in response.debug


@pytest.mark.smoke
def test_paul_murphy_identity_only_entity_unknown(crm_mvr_env: CoreStorage) -> None:
    response = run_query(EntityQuery(entity_key="Paul Murphy"))

    assert response.outcome == "entity_unknown"
    assert response.required_fields == ["employer"]
    assert response.results == []
    assert "employer" in response.message.lower()


@pytest.mark.smoke
def test_andrea_kalman_still_unresolved_not_unknown(crm_mvr_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(entity_key="Andrea Kalman", requested_attributes=["email"]),
    )

    assert response.outcome == "entity_key_unresolved"
    assert response.required_fields == []
    assert len(response.suggestions) == 1


@pytest.mark.smoke
def test_aaron_holiday_email_assembled_path(crm_mvr_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(entity_key="Aaron Holiday", requested_attributes=["email"]),
    )

    assert response.outcome == "assembled"
    assert response.required_fields == []
    assert response.suggestions == []
    assert "Aaron Holiday" in response.message or response.results


@pytest.mark.smoke
def test_nosuchperson_entity_unknown_not_not_found(crm_mvr_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(
            entity_key="NoSuchPerson-xyz",
            requested_attributes=["email"],
        ),
    )

    assert response.outcome == "entity_unknown"
    assert response.required_fields == ["employer"]
    assert response.suggestions == []
    assert response.results == []


@pytest.mark.smoke
def test_resolve_unknown_kind(crm_mvr_env: CoreStorage) -> None:
    _ = crm_mvr_env
    resolution = resolve_entity_key("Paul Murphy")
    assert resolution.kind == "unknown"
    assert resolution.suggestions == []


@pytest.mark.smoke
def test_empty_entity_key_stays_not_found(crm_mvr_env: CoreStorage) -> None:
    response = run_query(EntityQuery(entity_key="   ", requested_attributes=["email"]))

    assert response.outcome == "not_found"
    assert response.required_fields == []


@pytest.mark.smoke
def test_capabilities_exposes_mvr_and_entity_unknown_policy(
    crm_mvr_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_mvr_env
    capabilities = build_network_capabilities()
    policy = capabilities["policy"]
    assert "mvr" in policy
    assert policy["mvr"]["bind_fields"] == ["name", "employer"]
    assert "entity_unknown" in policy

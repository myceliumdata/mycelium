"""Smoke tests: MVR redesign M4 — field indexes and step-1 target resolve."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from agents.entity_registry import (
    RegistryEntity,
    get_entity_registry,
    reset_entity_registry,
)
from agents.field_index import intersect_lookup, normalize_field_index_value
from agents.classification import get_category_tree, reset_category_tree
from agents.context import reset_context_builder
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import get_delivery_store, reset_delivery_store
from network.paths import NetworkPaths
from network_helpers import apply_network_paths_monkeypatch, import_seed_for_test
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"
BASEBALL_MANIFEST = REPO_ROOT / "examples" / "networks" / "baseball" / "network.json"


@pytest.fixture
def crm_target_resolve_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()

    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")

    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(tmp_path / "deliveries.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_category_tree()
    get_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    storage = get_storage()
    import_seed_for_test(seed)
    _ = get_entity_registry()
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()

    yield storage

    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_field_index_normalization_matches_bind_rules() -> None:
    assert normalize_field_index_value("  Acme-Corp  ") == "acmecorp"


@pytest.mark.smoke
def test_field_index_and_lookup_intersection(crm_target_resolve_env: CoreStorage) -> None:
    _ = crm_target_resolve_env
    registry = get_entity_registry()
    by_employer = registry.lookup_by_target_lookup({"employer": "645 Ventures"})
    assert len(by_employer) == 3

    indexes = registry.field_indexes()
    assert len(intersect_lookup(indexes, {"employer": "645 Ventures"}, ["name", "employer"])) == 3

    single = registry.lookup_by_target_lookup(
        {"name": "Aaron Holiday", "employer": "645 Ventures"},
    )
    assert len(single) == 1


@pytest.mark.smoke
def test_target_resolve_by_id_lookup_resolved(crm_target_resolve_env: CoreStorage) -> None:
    _ = crm_target_resolve_env
    registry = get_entity_registry()
    entity_ids = registry.lookup_by_target_lookup(
        {"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
    )
    assert len(entity_ids) == 1
    entity_id = entity_ids[0]

    response = run_query(EntityQuery(id=entity_id))
    assert response.outcome == "lookup_resolved"
    assert response.total_matches == 1
    assert response.results == []
    assert response.delivery is not None
    assert response.delivery.delivery_id.startswith("d_")
    assert response.delivery.expires_at

    stored = get_delivery_store().get(response.delivery.delivery_id)
    assert stored is not None
    assert stored.entity_ids == [entity_id]
    assert stored.requested_attributes == []


@pytest.mark.smoke
def test_target_resolve_by_lookup_lookup_resolved(crm_target_resolve_env: CoreStorage) -> None:
    _ = crm_target_resolve_env
    response = run_query(
        EntityQuery(
            lookup={"employer": "HashCIB"},
            requested_attributes=["email"],
            provenance=True,
        ),
    )
    assert response.outcome == "lookup_resolved"
    assert response.total_matches == 3
    assert response.results == []
    assert response.delivery is not None

    stored = get_delivery_store().get(response.delivery.delivery_id)
    assert stored is not None
    assert len(stored.entity_ids) == 3
    assert stored.requested_attributes == ["email"]
    assert stored.provenance is True
    assert stored.lookup == {"employer": "HashCIB"}


@pytest.mark.smoke
def test_unknown_id_not_found_without_delivery(crm_target_resolve_env: CoreStorage) -> None:
    _ = crm_target_resolve_env
    missing_id = str(uuid.uuid4())
    response = run_query(EntityQuery(id=missing_id))
    assert response.outcome == "not_found"
    assert response.delivery is None
    assert response.total_matches is None
    assert "No record found for id" in response.message



@pytest.mark.smoke
def test_lookup_resolved_serializes_to_json(crm_target_resolve_env: CoreStorage) -> None:
    _ = crm_target_resolve_env
    response = run_query(EntityQuery(lookup={"employer": "Accel"}))
    payload = response.public_dict()
    assert payload["outcome"] == "lookup_resolved"
    assert payload["total_matches"] == 1
    assert payload["results"] == []
    assert payload["delivery"]["delivery_id"].startswith("d_")
    assert "create_on_deliver" not in payload["delivery"]
    assert "registry match" in response.message
    assert "step 2" in response.message


@pytest.mark.smoke
def test_create_pending_step1_json_has_create_on_deliver(
    crm_target_resolve_env: CoreStorage,
) -> None:
    _ = crm_target_resolve_env
    response = run_query(
        EntityQuery(
            lookup={"name": "Road Runner", "employer": "Acme Corp"},
        ),
    )
    assert response.outcome == "lookup_resolved"
    assert response.total_matches == 0
    assert response.delivery is not None
    assert response.delivery.create_on_deliver is True
    payload = response.public_dict()
    assert payload["delivery"]["create_on_deliver"] is True
    assert "step 2 will create" in response.message


@pytest.mark.smoke
def test_existing_match_step1_json_omits_create_on_deliver(
    crm_target_resolve_env: CoreStorage,
) -> None:
    _ = crm_target_resolve_env
    response = run_query(EntityQuery(lookup={"name": "Nichanan Kesonpat"}))
    assert response.outcome == "lookup_resolved"
    assert response.total_matches >= 1
    payload = response.public_dict()
    assert "create_on_deliver" not in payload.get("delivery", {})
    assert "registry match" in response.message


@pytest.mark.smoke
def test_baseball_player_alias_bind_step1_lookup_resolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    root = tmp_path / "baseball"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    paths = NetworkPaths.from_root(root)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    reset_entity_registry()
    reset_core_graph()
    reset_delivery_store()

    player = get_entity_registry(grain="player")
    entity = RegistryEntity(
        id="player-aaron",
        bind_values={"name": "Hank Aaron", "team": "Brooklyn Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    player.register_entity(entity)
    player.assign_bind_index(entity.id, entity.bind_values)
    player.save_entity(entity)
    player.add_bind_alias(
        entity.id,
        {"name": "Hank Aaron", "team": "Los Angeles Dodgers"},
    )

    response = run_query(
        EntityQuery(
            lookup={"name": "Hank Aaron", "team": "Los Angeles Dodgers"},
            grain="player",
        ),
    )
    assert response.outcome == "lookup_resolved"
    assert response.total_matches == 1
    assert response.delivery is not None
    stored = get_delivery_store().get(response.delivery.delivery_id)
    assert stored is not None
    assert stored.entity_ids == [entity.id]
    assert stored.grain == "player"

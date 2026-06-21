"""Smoke tests for classification-aware QueryResponse.message (MCP slice 3)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import reset_entity_registry
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from registry_helpers import resolve_and_deliver, step1_resolve, step2_deliver
from network_helpers import import_seed_for_test, copy_crm_network_manifest
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm-seeded" / "seed.json"


@pytest.fixture
def query_message_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """Isolated network with sample ontology and optional unknown attribute mappings."""
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()

    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "rows": [
                    {"name": "Test User", "employer": "Test Co"},
                ],
            },
        ),
        encoding="utf-8",
    )
    categories = json.loads(SAMPLE_CATEGORIES.read_text(encoding="utf-8"))
    categories["attribute_map"]["xyzzy_garbage"] = "unknown"
    categories_path = tmp_path / "categories.json"
    categories_path.write_text(json.dumps(categories), encoding="utf-8")
    copy_crm_network_manifest(tmp_path)

    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    reset_category_tree()
    from agents.classification import get_category_tree

    get_category_tree()
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_agent_registry()
    reset_agent_factory()
    storage = get_storage()
    import_seed_for_test(seed)

    yield storage

    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


@pytest.fixture
def kevin_multi_match_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """CRM-style seed with two Kevin Zhang records and sample ontology."""
    reset_storage()
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
    copy_crm_network_manifest(tmp_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))

    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    reset_category_tree()
    from agents.classification import get_category_tree

    get_category_tree()
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_agent_registry()
    reset_agent_factory()
    storage = get_storage()
    import_seed_for_test(seed)

    yield storage

    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_out_of_scope_only_no_researching_wording(
    query_message_env: CoreStorage,
) -> None:
    _ = query_message_env
    _step1, response = resolve_and_deliver(
        lookup={"name": "Test User"},
        requested_attributes=["xyzzy_garbage"],
    )

    assert len(response.results) == 1
    assert "does not appear related" in response.message
    assert "researching" not in response.message.lower()
    assert "may be in the future" not in response.message.lower()
    assert "out_of_scope=['xyzzy_garbage']" in response.debug


@pytest.mark.smoke
def test_mixed_in_scope_and_out_of_scope(
    query_message_env: CoreStorage,
) -> None:
    _ = query_message_env
    _step1, response = resolve_and_deliver(
        lookup={"name": "Test User"},
        requested_attributes=["email", "xyzzy_garbage"],
    )

    assert len(response.results) == 1
    assert "Classified email as contact" in response.message
    assert (
        "researching" in response.message.lower()
        or "setting up a contact specialist" in response.message.lower()
    )
    assert "does not appear related" in response.message
    assert "xyzzy_garbage" in response.message


@pytest.mark.smoke
def test_multi_match_collective_prefix(
    kevin_multi_match_env: CoreStorage,
) -> None:
    _ = kevin_multi_match_env
    _step1, response = resolve_and_deliver(
        lookup={"name": "Kevin Zhang"},
        requested_attributes=["email"],
    )

    assert len(response.results) == 2
    assert "Found 2 records for 'd_" in response.message
    assert "Classified email as contact" in response.message
    assert (
        "researching" in response.message.lower()
        or "setting up a contact specialist" in response.message.lower()
    )


@pytest.mark.smoke
def test_same_thread_new_query_rebuilds_response(
    query_message_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reusing thread_id with a different EntityQuery must not replay stale message."""
    _ = query_message_env
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()
    thread_id = "reuse-thread-checkpoint-bug"

    first_step1 = step1_resolve(
        lookup={"name": "Test User"},
        requested_attributes=["xyzzy_garbage"],
        thread_id=thread_id,
    )
    first = step2_deliver(first_step1.delivery.delivery_id, thread_id=thread_id)
    assert "does not appear related" in first.message
    assert "xyzzy_garbage" in first.message

    second_step1 = step1_resolve(
        lookup={"name": "Test User"},
        requested_attributes=["email"],
        thread_id=thread_id,
    )
    second = step2_deliver(second_step1.delivery.delivery_id, thread_id=thread_id)
    assert "does not appear related" not in second.message
    assert "xyzzy_garbage" not in second.message
    assert "Classified email as contact" in second.message
    assert "email" in second.debug


@pytest.mark.smoke
def test_not_found_neutral_lookup_wording(
    query_message_env: CoreStorage,
) -> None:
    _ = query_message_env
    response = run_query(EntityQuery(id="missing-id-xyz"))

    assert response.results == []
    assert response.outcome == "not_found"
    assert "missing-id-xyz" in response.message
    assert "anyone" not in response.message.lower()
    assert "did not match" not in response.message.lower()

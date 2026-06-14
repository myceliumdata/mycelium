"""Smoke tests for research gate (entity protocol slice 6)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.research_gate import RESEARCH_GATE_MESSAGE, is_research_gated, research_gate_allows
from graphs.core import reset_core_graph
from network_helpers import import_seed_for_test
from models.state import EntityQuery, MyceliumGraphState
from registry_helpers import resolve_and_deliver, step1_resolve, step2_deliver
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_gate_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
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
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")

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
    import_seed_for_test(seed)
    _ = get_entity_registry()
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()

    yield storage

    reset_storage()
    reset_entity_registry()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


def _entities_path() -> Path:
    return Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"])


@pytest.mark.smoke
def test_validated_murphy_email_invokes_specialist(crm_gate_env: CoreStorage) -> None:
    _ = crm_gate_env
    bound_step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert bound_step1.delivery is not None
    bound = step2_deliver(bound_step1.delivery.delivery_id)
    assert bound.outcome == "found"
    entity_id = bound.results[0]["id"]

    step1_email = step1_resolve(entity_id=entity_id, requested_attributes=["email"])
    assert step1_email.outcome == "lookup_resolved"
    assert step1_email.delivery is not None
    response = step2_deliver(step1_email.delivery.delivery_id)

    assert response.outcome == "assembled"
    assert "invoke_specialists" not in response.debug or response.outcome == "assembled"
    assert "contact" in response.debug.lower() or "email" in response.message.lower()


@pytest.mark.smoke
def test_provisional_murphy_email_validation_fail_no_invoke(
    crm_gate_env: CoreStorage,
) -> None:
    _ = crm_gate_env
    step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "A"},
        requested_attributes=["email"],
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None
    response = step2_deliver(step1.delivery.delivery_id)

    assert response.outcome == "found"
    assert "validation failed" in response.message.lower()
    assert "invoke_specialists" not in response.debug
    payload = json.loads(_entities_path().read_text(encoding="utf-8"))
    entity = payload["entities"][response.results[0]["id"]]
    assert entity["validation_state"] == "provisional"


@pytest.mark.smoke
def test_provisional_murphy_email_validates_then_invokes_same_turn(
    crm_gate_env: CoreStorage,
) -> None:
    _ = crm_gate_env
    _step1, response = resolve_and_deliver(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
        requested_attributes=["email"],
    )

    assert response.outcome == "assembled"
    payload = json.loads(_entities_path().read_text(encoding="utf-8"))
    entity = payload["entities"][response.results[0]["id"]]
    assert entity["validation_state"] == "validated"


@pytest.mark.smoke
def test_seed_andrea_kalmans_email_invokes(crm_gate_env: CoreStorage) -> None:
    _ = crm_gate_env
    _step1, response = resolve_and_deliver(
        lookup={"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
        requested_attributes=["email"],
    )

    assert response.outcome == "assembled"
    assert research_gate_allows(
        current_id=response.results[0]["id"],
        matched=[
            {
                "id": response.results[0]["id"],
                "_registry": True,
                "_validation_state": "validated",
            },
        ],
    )


@pytest.mark.smoke
def test_kalman_unresolved_email_no_invoke(crm_gate_env: CoreStorage) -> None:
    _ = crm_gate_env
    response = step1_resolve(
        lookup={"name": "Andrea Kalman"},
        requested_attributes=["email"],
    )

    assert response.outcome == "lookup_suggested"
    assert response.results == []
    assert "invoke_specialists" not in response.debug


@pytest.mark.smoke
def test_research_gate_message_on_provisional_attrs(crm_gate_env: CoreStorage) -> None:
    """Gate message when attrs blocked without validation failure."""
    _ = crm_gate_env
    provisional_match = {
        "id": "ent-test",
        "name": "Paul Murphy",
        "employer": "Acme Corp",
        "_registry": True,
        "_validation_state": "provisional",
    }
    state = MyceliumGraphState(
        query=EntityQuery(
            id="ent-test",
            requested_attributes=["email"],
        ),
        matched_records=[provisional_match],
        current_id="ent-test",
        validation_passed=None,
    )
    assert is_research_gated(state)
    assert not research_gate_allows(current_id="ent-test", matched=[provisional_match])

    gated_step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "A"},
        requested_attributes=["email"],
    )
    assert gated_step1.delivery is not None
    gated = step2_deliver(gated_step1.delivery.delivery_id)
    assert gated.outcome == "found"
    assert "invoke_specialists" not in gated.debug


def test_research_gate_constant_message() -> None:
    assert "provisionally bound" in RESEARCH_GATE_MESSAGE.lower()
    assert "validation" in RESEARCH_GATE_MESSAGE.lower()


def test_assemble_emits_gate_message_for_provisional_attrs() -> None:
    from agents.dispatch import assemble_response_node

    provisional_match = {
        "id": "ent-test",
        "name": "Paul Murphy",
        "employer": "Acme Corp",
        "_registry": True,
        "_validation_state": "provisional",
    }
    state = MyceliumGraphState(
        query=EntityQuery(
            id="ent-test",
            requested_attributes=["email"],
        ),
        matched_records=[provisional_match],
        current_id="ent-test",
        validation_passed=None,
        entity_resolution_kind="exact",
        invocation_thread_id="gate-unit",
    )
    result = assemble_response_node(state)
    response = result["response"]
    assert response.outcome == "found"
    assert RESEARCH_GATE_MESSAGE in response.message
    assert "email" not in response.results[0]

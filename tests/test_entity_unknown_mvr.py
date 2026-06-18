"""Smoke tests for lookup_incomplete / lookup_suggested + MVR policy."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import reset_entity_registry
from graphs.core import reset_core_graph, run_query
from network_helpers import import_seed_for_test
from models.state import EntityQuery
from network.introspection import build_network_capabilities
from network.mvr import MvrPolicy, load_mvr, missing_mvr_bind_fields
from registry_helpers import resolve_and_deliver
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
def test_load_mvr_from_network_json(crm_mvr_env: CoreStorage) -> None:
    _ = crm_mvr_env
    policy = load_mvr()
    assert policy.bind_fields == ["name", "employer"]
    assert missing_mvr_bind_fields({"name": "Paul Murphy"}, mvr=policy) == ["employer"]


@pytest.mark.smoke
def test_missing_mvr_bind_fields_partial_name(crm_mvr_env: CoreStorage) -> None:
    _ = crm_mvr_env
    assert missing_mvr_bind_fields({"name": "Paul"}) == ["employer"]


@pytest.mark.smoke
def test_missing_mvr_bind_fields_employer_only(crm_mvr_env: CoreStorage) -> None:
    _ = crm_mvr_env
    assert missing_mvr_bind_fields({"employer": "Acme"}) == ["name"]


@pytest.mark.smoke
def test_mvr_policy_has_no_legacy_bind_helpers() -> None:
    policy = MvrPolicy(bind_fields=["name", "employer"], description="test")
    assert not hasattr(policy, "required_bind_fields")
    assert not hasattr(policy, "required_fields_for_entity_key")
    assert not hasattr(policy, "allowed_binding_keys")


@pytest.mark.smoke
def test_paul_murphy_email_lookup_incomplete_no_specialists(
    crm_mvr_env: CoreStorage,
) -> None:
    response = run_query(
        EntityQuery(
            lookup={"name": "Paul Murphy"},
            requested_attributes=["email"],
        ),
    )

    assert response.outcome == "lookup_incomplete"
    assert response.required_fields == ["employer"]
    assert response.results == []
    assert response.suggestions == []
    assert "employer" in response.message.lower()
    assert "classified" not in response.debug.lower()
    assert "invoke_specialists" not in response.debug
    assert "outcome='lookup_incomplete'" in response.debug


@pytest.mark.smoke
def test_paul_murphy_identity_only_lookup_incomplete(crm_mvr_env: CoreStorage) -> None:
    response = run_query(EntityQuery(lookup={"name": "Paul Murphy"}))

    assert response.outcome == "lookup_incomplete"
    assert response.required_fields == ["employer"]
    assert response.results == []
    assert "employer" in response.message.lower()


@pytest.mark.smoke
def test_andrea_kalman_lookup_suggested(crm_mvr_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(
            lookup={"name": "Andrea Kalman"},
            requested_attributes=["email"],
        ),
    )

    assert response.outcome == "lookup_suggested"
    assert response.required_fields == []
    assert len(response.suggestions) == 1


@pytest.mark.smoke
def test_aaron_holiday_email_assembled_path(crm_mvr_env: CoreStorage) -> None:
    _step1, step2 = resolve_and_deliver(
        lookup={"name": "Aaron Holiday", "employer": "645 Ventures"},
        requested_attributes=["email"],
    )

    assert step2.outcome == "assembled"
    assert step2.required_fields == []
    assert step2.suggestions == []
    assert "Aaron Holiday" in step2.message or step2.results


@pytest.mark.smoke
def test_nosuchperson_lookup_incomplete(crm_mvr_env: CoreStorage) -> None:
    response = run_query(
        EntityQuery(
            lookup={"name": "NoSuchPerson-xyz"},
            requested_attributes=["email"],
        ),
    )

    assert response.outcome == "lookup_incomplete"
    assert response.required_fields == ["employer"]
    assert response.suggestions == []
    assert response.results == []


@pytest.mark.smoke
def test_empty_lookup_rejected_at_model(crm_mvr_env: CoreStorage) -> None:
    from pydantic import ValidationError

    _ = crm_mvr_env
    with pytest.raises(ValidationError):
        EntityQuery(lookup={}, requested_attributes=["email"])


@pytest.mark.smoke
def test_capabilities_exposes_mvr_policy(crm_mvr_env: CoreStorage) -> None:
    _ = crm_mvr_env
    capabilities = build_network_capabilities()
    policy = capabilities["policy"]
    assert "mvr" in policy
    assert policy["mvr"]["default_record_type"] == "person"
    assert policy["mvr"]["record_types"]["person"]["bind_fields"] == ["name", "employer"]

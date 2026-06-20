"""Smoke tests: target step-1 lookup clarity (incomplete, suggested, confirm)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import reset_delivery_store
from network.example import refresh_example_network
from network_helpers import import_seed_for_test
from storage.core import CoreStorage, get_storage, reset_storage
from test_example_network_capstones import run_create_on_deliver

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_lookup_clarity_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()

    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
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
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_category_tree()
    get_category_tree()
    storage = get_storage()
    import_seed_for_test(seed)
    _ = get_entity_registry()
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
def test_partial_fuzzy_employer_lookup_suggested(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"employer": "654 Ventures"}))
    assert response.outcome == "lookup_suggested"
    assert response.total_matches == 0
    assert response.delivery is None
    assert len(response.suggestions) >= 1
    assert response.suggestions[0].suggested_lookup == {"employer": "645 Ventures"}
    assert response.suggestions[0].suggested_lookup.get("employer") == "645 Ventures"
    assert response.suggestions[0].reason == "fuzzy_bind_field_match"


@pytest.mark.smoke
def test_partial_fuzzy_employer_plural_typo_suggests_employer(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"employer": "645 Venture"}))
    assert response.outcome == "lookup_suggested"
    assert response.total_matches == 0
    assert response.delivery is None
    assert response.suggestions[0].suggested_lookup == {"employer": "645 Ventures"}
    assert response.suggestions[0].suggested_lookup.get("employer") == "645 Ventures"
    assert response.suggestions[0].reason == "fuzzy_bind_field_match"


@pytest.mark.smoke
def test_partial_fuzzy_employer_with_attrs_still_suggested(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(
        EntityQuery(
            lookup={"employer": "645 Venture"},
            requested_attributes=["title", "email"],
        ),
    )
    assert response.outcome == "lookup_suggested"
    assert response.total_matches == 0
    assert response.delivery is None
    assert response.suggestions[0].suggested_lookup == {"employer": "645 Ventures"}
    assert response.suggestions[0].suggested_lookup.get("employer") == "645 Ventures"


@pytest.mark.smoke
def test_partial_fuzzy_employer_retry_then_resolved(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    typo = run_query(
        EntityQuery(
            lookup={"employer": "645 Venture"},
            requested_attributes=["title", "email"],
        ),
    )
    assert typo.outcome == "lookup_suggested"
    assert typo.delivery is None

    resolved = run_query(
        EntityQuery(
            lookup={"employer": "645 Ventures"},
            requested_attributes=["title", "email"],
        ),
    )
    assert resolved.outcome == "lookup_resolved"
    assert resolved.total_matches == 3
    assert resolved.delivery is not None


@pytest.mark.smoke
def test_partial_employer_shorthand_lookup_suggested(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"employer": "645"}))
    assert response.outcome == "lookup_suggested"
    assert response.total_matches == 0
    assert response.delivery is None
    assert response.suggestions[0].suggested_lookup == {"employer": "645 Ventures"}
    assert response.suggestions[0].reason == "fuzzy_bind_field_match"


@pytest.mark.smoke
def test_partial_fuzzy_name_lookup_suggested(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"name": "Andrea Kalman"}))
    assert response.outcome == "lookup_suggested"
    assert response.total_matches == 0
    assert response.delivery is None
    assert len(response.suggestions) >= 1
    assert response.suggestions[0].suggested_lookup == {"name": "Andrea Kalmans"}
    assert response.suggestions[0].reason == "fuzzy_bind_field_match"


@pytest.mark.smoke
def test_partial_lookup_missing_employer_lookup_incomplete(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"name": "Paul Murphy"}))
    assert response.outcome == "lookup_incomplete"
    assert response.total_matches == 0
    assert response.delivery is None
    assert "employer" in response.required_fields

    payload = response.public_dict()
    assert payload["outcome"] == "lookup_incomplete"
    assert "employer" in payload["required_fields"]
    assert "delivery" not in payload
    assert "suggestions" not in payload


@pytest.mark.smoke
def test_partial_lookup_name_hit_lookup_resolved(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"name": "Andrea Kalmans"}))
    assert response.outcome == "lookup_resolved"
    assert response.total_matches >= 1
    assert response.delivery is not None


@pytest.mark.smoke
def test_full_mvr_wrong_employer_lookup_suggested(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(
        EntityQuery(lookup={"name": "Andrea Kalmans", "employer": "Wrong Corp"}),
    )
    assert response.outcome == "lookup_suggested"
    assert response.total_matches == 0
    assert response.delivery is None
    assert len(response.suggestions) >= 1
    assert any(
        item.reason == "same_bind_field_conflict"
        for item in response.suggestions
    )
    assert any(
        item.suggested_lookup.get("employer") == "Lontra Ventures"
        for item in response.suggestions
    )

    payload = response.public_dict()
    assert payload["outcome"] == "lookup_suggested"
    assert "delivery" not in payload
    assert len(payload["suggestions"]) >= 1


@pytest.mark.smoke
def test_full_mvr_wrong_employer_confirm_creates(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(
        EntityQuery(
            lookup={"name": "Andrea Kalmans", "employer": "Wrong Corp"},
            confirm_new_entity=True,
        ),
    )
    assert response.outcome == "lookup_resolved"
    assert response.total_matches == 0
    assert response.delivery is not None
    assert response.delivery.create_on_deliver is True


@pytest.mark.smoke
def test_full_mvr_no_collision_create(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(
        EntityQuery(lookup={"name": "Road Runner", "employer": "Acme Corp"}),
    )
    assert response.outcome == "lookup_resolved"
    assert response.total_matches == 0
    assert response.delivery is not None
    assert response.delivery.create_on_deliver is True


@pytest.mark.smoke
def test_fuzzy_name_lookup_suggested(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(
        EntityQuery(lookup={"name": "Andrea Kalman", "employer": "Acme Corp"}),
    )
    assert response.outcome == "lookup_suggested"
    assert response.delivery is None
    assert len(response.suggestions) >= 1
    assert response.suggestions[0].reason == "fuzzy_bind_field_match"
    assert response.suggestions[0].suggested_lookup == {"name": "Andrea Kalmans"}


@pytest.mark.smoke
def test_empty_crm_safe_create_without_confirm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "empty-crm-clarity"
    refresh_example_network("empty-crm", root=target, register=False, yes=True)
    outcome = run_create_on_deliver(
        monkeypatch,
        target,
        {"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert outcome["step1"].outcome == "lookup_resolved"
    assert outcome["step1"].delivery is not None
    assert outcome["step1"].delivery.create_on_deliver is True


@pytest.mark.smoke
def test_public_json_suggestions_exclude_entity_key(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"name": "Andrea Kalman"}))
    payload = response.public_dict()
    assert payload["outcome"] == "lookup_suggested"
    suggestion = payload["suggestions"][0]
    assert "entity_key" not in suggestion
    assert suggestion["suggested_lookup"] == {"name": "Andrea Kalmans"}


@pytest.mark.smoke
def test_name_fuzzy_suggested_lookup_shape(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"name": "Andrea Kalman"}))
    assert response.suggestions[0].suggested_lookup == {"name": "Andrea Kalmans"}
    payload = response.public_dict()
    assert payload["suggestions"][0]["suggested_lookup"] == {"name": "Andrea Kalmans"}
    assert payload["suggestions"][0].get("id")


@pytest.mark.smoke
def test_employer_fuzzy_suggested_lookup_shape(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(EntityQuery(lookup={"employer": "645 Venture"}))
    assert response.suggestions[0].suggested_lookup == {"employer": "645 Ventures"}
    payload = response.public_dict()
    suggestion = payload["suggestions"][0]
    assert suggestion["suggested_lookup"] == {"employer": "645 Ventures"}
    assert suggestion["reason"] == "fuzzy_bind_field_match"
    assert "id" not in suggestion
    assert "name" not in suggestion


@pytest.mark.smoke
def test_same_bind_field_conflict_suggested_lookup(
    crm_lookup_clarity_env: CoreStorage,
) -> None:
    _ = crm_lookup_clarity_env
    response = run_query(
        EntityQuery(lookup={"name": "Andrea Kalmans", "employer": "Wrong Corp"}),
    )
    lontra = next(
        item
        for item in response.suggestions
        if item.suggested_lookup.get("employer") == "Lontra Ventures"
    )
    assert lontra.suggested_lookup == {
        "name": "Andrea Kalmans",
        "employer": "Lontra Ventures",
    }


@pytest.mark.smoke
def test_confirm_new_entity_rejected_on_step2() -> None:
    with pytest.raises(ValueError, match="confirm_new_entity is step 1 only"):
        EntityQuery(delivery_id="d_abc", confirm_new_entity=True)

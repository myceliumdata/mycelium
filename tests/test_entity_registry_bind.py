"""Smoke tests for entity registry + provisional bind (entity protocol slice 4)."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import (
    EntityRegistry,
    LegacyEntitiesSchemaError,
    get_entity_registry,
    make_bind_key,
    reset_entity_registry,
)
from graphs.core import reset_core_graph
from models.state import EntityQuery
from network_helpers import copy_crm_network_manifest, import_seed_for_test
from network.paths import NetworkPaths
from registry_helpers import lookup_entities_by_name, resolve_and_deliver, step1_resolve, step2_deliver
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_registry_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """Isolated CRM network with MVR and empty entities.json."""
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


@pytest.mark.smoke
def test_murphy_bind_creates_provisional_entity(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    entities_path = Path(
        __import__("os").environ["MYCELIUM_ENTITIES_PATH"],
    )

    step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None
    response = step2_deliver(step1.delivery.delivery_id)

    assert response.outcome == "found"
    assert response.required_fields == []
    assert len(response.results) == 1
    assert response.results[0]["name"] == "Paul Murphy"
    assert response.results[0]["employer"] == "Acme Corp"
    assert response.results[0]["id"]
    assert response.message == "Core record validated."
    assert entities_path.is_file()
    payload = json.loads(entities_path.read_text(encoding="utf-8"))
    assert "paul murphy|acme corp" in payload["bind_index"]
    murphy_id = payload["bind_index"]["paul murphy|acme corp"]
    murphy = payload["entities"][murphy_id]
    assert murphy["source"] == "query_bind"
    assert murphy["validation_state"] == "validated"


@pytest.mark.smoke
def test_repeat_bind_is_idempotent_found(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    first_step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert first_step1.delivery is not None
    first = step2_deliver(first_step1.delivery.delivery_id)
    assert first.outcome == "found"
    first_id = first.results[0]["id"]

    second = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert second.outcome == "lookup_resolved"
    assert second.delivery is not None
    second_delivered = step2_deliver(second.delivery.delivery_id)
    assert second_delivered.outcome == "found"
    assert second_delivered.results[0]["id"] == first_id

    entities_path = Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"])
    payload = json.loads(entities_path.read_text(encoding="utf-8"))
    assert payload["bind_index"]["paul murphy|acme corp"] == first_id


@pytest.mark.smoke
def test_name_only_two_registry_rows_requires_employer(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    step1a = step1_resolve(lookup={"name": "Paul Murphy", "employer": "Acme Corp"})
    assert step1a.delivery is not None
    step2_deliver(step1a.delivery.delivery_id)
    step1b = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Beta LLC"},
        confirm_new_entity=True,
    )
    assert step1b.delivery is not None
    step2_deliver(step1b.delivery.delivery_id)

    response = step1_resolve(
        lookup={"name": "Paul Murphy"},
        requested_attributes=["email"],
    )

    assert response.outcome == "lookup_resolved"
    assert response.delivery is not None
    delivered = step2_deliver(response.delivery.delivery_id)
    assert delivered.outcome == "assembled"
    assert delivered.results
    from agents.supervisor import supervisor_agent
    from models.state import MyceliumGraphState

    planned = supervisor_agent(
        MyceliumGraphState(
            query=EntityQuery(
                lookup={"name": "Paul Murphy"},
                requested_attributes=["email"],
            ),
        ),
    )
    assert planned["context"]["_meta"]["specialists_to_invoke"] == []


@pytest.mark.smoke
def test_same_name_different_employers_get_two_ids(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env

    acme_step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert acme_step1.delivery is not None
    acme = step2_deliver(acme_step1.delivery.delivery_id)
    beta_step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Beta LLC"},
        confirm_new_entity=True,
    )
    assert beta_step1.delivery is not None
    beta = step2_deliver(beta_step1.delivery.delivery_id)

    assert acme.outcome == "found"
    assert beta.outcome == "found"
    assert acme.results[0]["id"] != beta.results[0]["id"]

    payload = json.loads(
        Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"]).read_text(),
    )
    assert "paul murphy|acme corp" in payload["bind_index"]
    assert "paul murphy|beta llc" in payload["bind_index"]
    assert (
        payload["bind_index"]["paul murphy|acme corp"]
        != payload["bind_index"]["paul murphy|beta llc"]
    )


@pytest.mark.smoke
def test_murphy_bound_plus_email_no_specialist_invoke(
    crm_registry_env: CoreStorage,
) -> None:
    _ = crm_registry_env
    _step1, bound = resolve_and_deliver(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
        requested_attributes=["email"],
    )
    assert bound.outcome == "assembled"
    assert bound.results[0]["id"]
    payload = json.loads(
        Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"]).read_text(),
    )
    murphy = payload["entities"][payload["bind_index"]["paul murphy|acme corp"]]
    assert murphy["validation_state"] == "validated"

    entity_id = bound.results[0]["id"]
    follow_up = step1_resolve(
        entity_id=entity_id,
        requested_attributes=["email"],
    )
    assert follow_up.outcome == "lookup_resolved"
    assert follow_up.delivery is not None
    follow_up_step2 = step2_deliver(follow_up.delivery.delivery_id)
    assert follow_up_step2.outcome == "assembled"
    assert follow_up_step2.results[0]["id"] == entity_id


@pytest.mark.smoke
def test_aaron_holiday_seed_creates_registry_mirror(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    entities_path = Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"])

    aaron_seed = lookup_entities_by_name("Aaron Holiday")
    assert aaron_seed
    _step1, response = resolve_and_deliver(
        lookup={
            "name": "Aaron Holiday",
            "employer": str(aaron_seed[0]["employer"]),
        },
        requested_attributes=["email"],
    )

    assert response.outcome == "assembled"
    assert entities_path.is_file()
    payload = json.loads(entities_path.read_text(encoding="utf-8"))
    aaron = next(
        entity
        for entity in payload["entities"].values()
        if entity["bind_values"]["name"] == "Aaron Holiday"
    )
    assert aaron["source"] == "seed_bootstrap"
    assert aaron["validation_state"] == "validated"


@pytest.mark.smoke
def test_partial_binding_under_specified(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    response = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": ""},
        requested_attributes=["email"],
    )

    assert response.outcome == "lookup_incomplete"
    assert response.required_fields == ["employer"]
    assert response.results == []


@pytest.mark.smoke
def test_uuid_lookup_after_bind(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    bound_step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert bound_step1.delivery is not None
    bound = step2_deliver(bound_step1.delivery.delivery_id)
    entity_id = bound.results[0]["id"]

    resolution = step1_resolve(entity_id=entity_id)
    assert resolution.outcome == "lookup_resolved"
    assert resolution.delivery is not None
    resolution_step2 = step2_deliver(resolution.delivery.delivery_id)
    assert resolution_step2.outcome == "found"
    assert resolution_step2.results[0]["id"] == entity_id


@pytest.mark.smoke
def test_bind_index_lookup_by_name_and_binding(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    bound_step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert bound_step1.delivery is not None
    bound = step2_deliver(bound_step1.delivery.delivery_id)
    entity_id = bound.results[0]["id"]

    by_name = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert by_name.outcome == "lookup_resolved"
    assert by_name.delivery is not None
    by_name_step2 = step2_deliver(by_name.delivery.delivery_id)
    assert by_name_step2.outcome == "found"
    assert by_name_step2.results[0]["id"] == entity_id


@pytest.mark.smoke
def test_unknown_binding_keys_ignored(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp", "malicious": "x"},
    )
    assert step1.outcome == "lookup_resolved"
    assert step1.delivery is not None
    response = step2_deliver(step1.delivery.delivery_id)
    assert response.outcome == "found"


@pytest.mark.smoke
def test_missing_uuid_stays_not_found(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    missing_id = str(uuid.uuid4())
    response = step1_resolve(entity_id=missing_id)
    assert response.outcome == "not_found"


@pytest.mark.smoke
def test_ensure_bound_entity_allocates_uuid4(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    copy_crm_network_manifest(tmp_path)
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    reset_category_tree()
    reset_entity_registry()
    registry = get_entity_registry()
    entity, duplicate = registry.ensure_bound_entity(
        "Test Person",
        "Acme",
        source="seed_bootstrap",
        validation_state="validated",
    )
    assert duplicate is False
    uuid.UUID(entity.id)
    assert entity.source == "seed_bootstrap"


@pytest.mark.smoke
def test_ensure_bound_entity_duplicate_preserves_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    copy_crm_network_manifest(tmp_path)
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    reset_category_tree()
    reset_entity_registry()
    registry = get_entity_registry()
    seed_row, _ = registry.ensure_bound_entity(
        "Andrea Kalmans",
        "Example Co",
        source="seed_bootstrap",
        validation_state="validated",
    )
    bind_row, duplicate = registry.bind_provisional("Andrea Kalmans", "Example Co")
    assert duplicate is True
    assert bind_row.id == seed_row.id
    assert bind_row.source == "seed_bootstrap"


@pytest.mark.smoke
def test_lookup_entities_by_key_stable_after_reimport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "people": [
                    {"name": "Andrea Kalmans", "employer": "Example Co"},
                ],
            },
        ),
        encoding="utf-8",
    )
    copy_crm_network_manifest(tmp_path)
    entities_path = NetworkPaths.from_root(tmp_path).entities_path
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))

    import_seed_for_test(seed)
    first_id = lookup_entities_by_name("Andrea Kalmans")[0]["id"]

    import_seed_for_test(seed)
    second_id = lookup_entities_by_name("Andrea Kalmans")[0]["id"]

    assert first_id == second_id
    assert entities_path.is_file()


@pytest.mark.smoke
def test_registry_entity_json_omits_top_level_name_employer(
    crm_registry_env: CoreStorage,
) -> None:
    _ = crm_registry_env
    step1 = step1_resolve(
        lookup={"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert step1.delivery is not None
    step2_deliver(step1.delivery.delivery_id)
    payload = json.loads(
        Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"]).read_text(
            encoding="utf-8",
        ),
    )
    murphy_id = payload["bind_index"]["paul murphy|acme corp"]
    murphy = payload["entities"][murphy_id]
    assert "bind_values" in murphy
    assert murphy["bind_values"]["name"] == "Paul Murphy"
    assert murphy["bind_values"]["employer"] == "Acme Corp"
    assert "name" not in murphy
    assert "employer" not in murphy


@pytest.mark.smoke
def test_make_bind_key_respects_bind_fields_order() -> None:
    values = {"name": "Ada", "employer": "Lab"}
    assert make_bind_key(values, ["name", "employer"]) == "ada|lab"
    assert make_bind_key(values, ["employer", "name"]) == "lab|ada"


@pytest.mark.smoke
def test_make_bind_key_partial_bind_values_raises() -> None:
    with pytest.raises(ValueError, match="missing or empty MVR fields"):
        make_bind_key({"name": "Ada"}, ["name", "employer"])


@pytest.mark.smoke
def test_lookup_by_bind_values_requires_full_mvr(crm_registry_env: CoreStorage) -> None:
    _ = crm_registry_env
    registry = get_entity_registry()
    with pytest.raises(ValueError, match="missing or empty MVR fields"):
        registry.lookup_by_bind_values({"name": "Paul Murphy"})


@pytest.mark.smoke
def test_legacy_entities_json_load_fails_loud(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entities_path = tmp_path / "entities.json"
    copy_crm_network_manifest(tmp_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    entities_path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "entities": {
                    "legacy-id": {
                        "id": "legacy-id",
                        "name": "Paul Murphy",
                        "employer": "Acme Corp",
                        "validation_state": "validated",
                    },
                },
                "bind_index": {},
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(entities_path))
    reset_entity_registry()
    with pytest.raises(LegacyEntitiesSchemaError, match="refresh-example-network"):
        EntityRegistry(path=entities_path)

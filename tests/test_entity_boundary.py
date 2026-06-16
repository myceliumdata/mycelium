"""Smoke tests for seed vs specialist storage boundary (entity protocol slice 7)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from agents.classification import reset_category_tree
from agents.context import ContextBuilder, strip_bind_fields
from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
from agents.specialists.fields import current_status
from agents.registry import get_agent_registry, reset_agent_registry
from agents.entity_registry import reset_entity_registry
from graphs.core import reset_core_graph, run_query
from network_helpers import copy_crm_network_manifest, import_seed_for_test
from models.state import EntityQuery, MyceliumGraphState
from registry_helpers import lookup_entities_by_name
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_boundary_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_agent_registry()
    reset_agent_factory()
    reset_core_graph()
    reset_category_tree()

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
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()

    yield storage

    reset_storage()
    reset_entity_registry()
    reset_agent_registry()
    reset_agent_factory()
    reset_core_graph()
    reset_category_tree()


@pytest.mark.smoke
def test_factory_storage_record_has_no_bind_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reg_path = tmp_path / "reg.json"
    specialists_dir = tmp_path / "specialists"
    data_dir = tmp_path / "agent_data"
    monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(reg_path))
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(specialists_dir))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(data_dir))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    reset_agent_registry()
    reset_agent_factory()

    factory = get_agent_factory()
    factory.create_specialist(
        "contact",
        "contact_specialist",
        "Direct contact info",
        auto_commit=False,
    )
    fn = get_agent_registry().get_agent_fn("contact_specialist")
    assert fn is not None
    test_id = "boundary-test-uuid"
    fn(
        MyceliumGraphState(
            query=EntityQuery(id=test_id, requested_attributes=["email"]),
            current_id=test_id,
            context={
                "entity_id": test_id,
                "bind": {"name": "Test", "employer": "Co"},
                "specialists": {},
            },
            target_fields=["email"],
        ),
    )
    stored = json.loads((data_dir / "contact" / "storage.json").read_text(encoding="utf-8"))
    rec = stored["records"][test_id]
    assert "name" not in rec
    assert "employer" not in rec
    assert current_status(rec["email"]) == "pending"


@pytest.mark.smoke
def test_build_context_uses_bind_and_strips_legacy_storage_fields(
    crm_boundary_env: CoreStorage,
) -> None:
    _ = crm_boundary_env
    bind_row = {"id": "ent-1", "name": "Paul Murphy", "employer": "Acme Corp"}
    builder = ContextBuilder()
    ctx = builder.build_full_context(
        ["ent-1"],
        matched_records=[
            {
                **bind_row,
                "_registry": True,
                "_validation_state": "validated",
            },
        ],
    )
    assert ctx["entity_id"] == "ent-1"
    assert ctx["bind"] == {"name": "Paul Murphy", "employer": "Acme Corp"}
    assert "seed" not in ctx


@pytest.mark.smoke
def test_build_context_resolves_bind_from_registry_by_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.entity_registry import get_entity_registry, reset_entity_registry

    entities = tmp_path / "entities.json"
    categories_path = tmp_path / "categories.json"
    copy_crm_network_manifest(tmp_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(entities))
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    reset_category_tree()
    reset_entity_registry()
    registry = get_entity_registry()
    entity, _ = registry.ensure_bound_entity(
        "Paul Murphy",
        "Acme Corp",
        source="query_bind",
        validation_state="validated",
    )

    ctx = ContextBuilder().build_full_context([entity.id])

    assert ctx["entity_id"] == entity.id
    assert ctx["bind"] == {"name": "Paul Murphy", "employer": "Acme Corp"}


def test_strip_bind_fields_ignores_legacy_keys() -> None:
    stripped = strip_bind_fields(
        {
            "name": "Legacy",
            "employer": "Old Co",
            "email": {"status": "found", "value": "a@b.com"},
        },
    )
    assert stripped == {"email": {"status": "found", "value": "a@b.com"}}


@pytest.mark.smoke
def test_validated_entity_email_research_receives_bind_context(
    crm_boundary_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_boundary_env
    captured: dict[str, Any] = {}

    def _capture_research(**kwargs: Any) -> Any:
        captured.update(kwargs)
        from tools.research import ResearchRunResult

        return ResearchRunResult()

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _capture_research)

    matches = lookup_entities_by_name("Andrea Kalmans")
    entity_id = next(row["id"] for row in matches if row.get("employer") == "Lontra Ventures")
    bound = run_query(EntityQuery(id=entity_id))
    assert bound.outcome == "lookup_resolved"
    assert bound.delivery is not None
    run_query(EntityQuery(delivery_id=bound.delivery.delivery_id))
    with_email = run_query(EntityQuery(id=entity_id, requested_attributes=["email"]))
    assert with_email.outcome == "lookup_resolved"
    assert with_email.delivery is not None
    run_query(EntityQuery(delivery_id=with_email.delivery.delivery_id))

    assert captured.get("person_id") == entity_id
    ctx = captured.get("context") or {}
    assert ctx.get("entity_id") == entity_id
    assert ctx.get("bind", {}).get("name") == "Andrea Kalmans"
    assert "seed" not in ctx


def test_no_runtime_core_identity_imports() -> None:
    src = REPO_ROOT / "src"
    offenders: list[str] = []
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "core_identity" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []

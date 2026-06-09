"""Smoke tests for network growth and registry attribution (entity protocol slice 8)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_growth import parse_research_fields_updated
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.seed import reset_seed_data
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from storage.core import CoreStorage, get_storage, reset_storage
from tools.research import ResearchRunResult

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"


@pytest.fixture
def crm_growth_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
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
    storage.seed_from_file(seed)
    reset_seed_data()
    reset_entity_registry()
    _ = get_entity_registry()
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    reset_core_graph()

    yield storage

    reset_storage()
    reset_seed_data()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


def _entities_path() -> Path:
    return Path(__import__("os").environ["MYCELIUM_ENTITIES_PATH"])


def _mock_email_research(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        storage: Any,
        llm: Any | None = None,
    ) -> ResearchRunResult:
        _ = category, specialist_name, context, llm
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        for field in target_fields:
            rec[field] = {
                "status": "found",
                "value": "paul.murphy@acme.example",
                "confidence": 0.9,
                "sources": ["https://example.com/paul"],
                "researched_at": now,
            }
        storage.save(data)
        return ResearchRunResult(fields_updated=list(target_fields), tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)


def test_parse_research_fields_updated() -> None:
    audit = [
        "contact_specialist: found for id='x' (category=contact).",
        "contact_specialist: research id=x fields=['email'] updated=['email'] tool_calls=1 errors=0",
    ]
    assert parse_research_fields_updated(audit) == ["email"]


def test_attribution_uses_researched_fields_without_audit() -> None:
    from agents.entity_growth import apply_registry_research_attribution
    from agents.entity_registry import EntityRegistry

    path = REPO_ROOT / "tmp-entity-growth-test.json"
    if path.exists():
        path.unlink()
    reg = EntityRegistry(path=path)
    entity, _ = reg.bind_provisional("Paul Murphy", "Acme Corp")
    reg.promote_validated(entity.id)

    logs = apply_registry_research_attribution(
        entity_id=entity.id,
        contributions=[
            {
                "specialist_contrib": {
                    "category": "contact",
                    "researched_fields": ["email"],
                },
                "researched_fields": ["email"],
            },
        ],
    )
    assert logs
    updated = reg.lookup_by_id(entity.id)
    assert updated is not None
    assert updated.attr_sources["email"] == "contact"
    path.unlink(missing_ok=True)


@pytest.mark.smoke
def test_paul_murphy_full_growth_arc(crm_growth_env: CoreStorage, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = crm_growth_env
    _mock_email_research(monkeypatch)

    unknown = run_query(
        EntityQuery(entity_key="Paul Murphy", requested_attributes=["email"]),
    )
    assert unknown.outcome == "entity_unknown"
    assert unknown.required_fields == ["employer"]

    bound = run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"}),
    )
    assert bound.outcome == "entity_validated"
    entity_id = bound.results[0]["id"]

    researched = run_query(
        EntityQuery(
            entity_key=entity_id,
            requested_attributes=["email"],
        ),
    )
    assert researched.outcome == "assembled"

    payload = json.loads(_entities_path().read_text(encoding="utf-8"))
    entity = payload["entities"][entity_id]
    assert entity["validation_state"] == "validated"
    assert entity["attr_sources"]["email"] == "contact"
    assert entity["last_researched_at"]["email"]

    requery = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )
    assert requery.outcome == "assembled"
    assert requery.results[0]["id"] == entity_id
    assert requery.results[0].get("email") == "paul.murphy@acme.example"


@pytest.mark.smoke
def test_seed_person_unchanged_after_registry_growth(
    crm_growth_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = crm_growth_env
    _mock_email_research(monkeypatch)

    run_query(
        EntityQuery(entity_key="Paul Murphy", binding={"employer": "Acme Corp"}),
    )
    run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            binding={"employer": "Acme Corp"},
            requested_attributes=["email"],
        ),
    )

    andrea = run_query(
        EntityQuery(entity_key="Andrea Kalmans", requested_attributes=["email"]),
    )
    assert andrea.outcome == "assembled"

    entities_path = _entities_path()
    payload = json.loads(entities_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 1
    murphy = next(iter(payload["entities"].values()))
    assert murphy["name"] == "Paul Murphy"
    assert "Andrea Kalmans" not in {e["name"] for e in payload["entities"].values()}

"""End-to-end capstone smoke tests: refresh_example_network → production-shaped outcomes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agents.classification import reset_category_tree
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from agents.specialists.base import SpecialistStorage
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import reset_delivery_store
from network.example import refresh_example_network
from network.paths import NetworkPaths, apply_network_paths
from storage.core import reset_storage

ROAD_RUNNER_LOOKUP: dict[str, str] = {"name": "Road Runner", "employer": "Acme Corp"}
PAUL_MURPHY_LOOKUP: dict[str, str] = {"name": "Paul Murphy", "employer": "Acme Corp"}


def reset_query_runtime() -> None:
    """Clear process singletons before in-process ``run_query`` on a refreshed root."""
    for reset_fn in (
        reset_storage,
        reset_entity_registry,
        reset_core_graph,
        reset_category_tree,
        reset_delivery_store,
        reset_agent_registry,
        reset_agent_factory,
    ):
        reset_fn()


def apply_refreshed_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    """Point runtime env at a live refreshed network root (no extra bootstrap helpers)."""
    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    reset_query_runtime()
    reset_core_graph()


def assert_crm_seed_capstone(target: Path) -> None:
    """Post-refresh CRM: 15 entities and seed_bootstrap bind versions in specialist storage."""
    entities_path = target / "entities.json"
    assert entities_path.is_file()
    payload = json.loads(entities_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 15
    assert len(payload["bind_index"]) == 15

    demographic = json.loads(
        (target / "agents" / "demographic" / "storage.json").read_text(encoding="utf-8"),
    )
    professional = json.loads(
        (target / "agents" / "professional" / "storage.json").read_text(encoding="utf-8"),
    )
    assert len(demographic.get("records", {})) == 15
    assert len(professional.get("records", {})) == 15
    first_id = next(iter(payload["entities"]))
    name_entry = demographic["records"][first_id]["name"]
    assert name_entry["versions"][0]["actor"]["kind"] == "seed_bootstrap"


def assert_bind_storage(
    *,
    entity_id: str,
    actor_kind: str,
    name_version_count: int = 1,
) -> None:
    """Assert demographic + professional bind versions for one entity (in-process paths)."""
    demographic = SpecialistStorage("demographic")
    professional = SpecialistStorage("professional")
    demo_records = demographic.load().get("records") or {}
    prof_records = professional.load().get("records") or {}
    assert entity_id in demo_records
    assert entity_id in prof_records
    name_entry = demo_records[entity_id]["name"]
    employer_entry = prof_records[entity_id]["employer"]
    assert len(name_entry.get("versions") or []) == name_version_count
    assert name_entry["versions"][0]["actor"]["kind"] == actor_kind
    assert employer_entry["versions"][0]["actor"]["kind"] == actor_kind


def run_create_on_deliver(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    lookup: dict[str, str],
) -> dict[str, Any]:
    """Step 1 + step 2 create-on-deliver; return step responses and created entity id."""
    apply_refreshed_root(monkeypatch, root)
    registry = get_entity_registry()
    before_ids = {entity.id for entity in registry.list_entities()}

    step1 = run_query(EntityQuery(lookup=lookup))
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 0
    assert step1.delivery is not None
    assert step1.delivery.create_on_deliver is True

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert len(step2.results) == 1
    created = step2.results[0]
    assert created["id"] not in before_ids

    return {
        "step1": step1,
        "step2": step2,
        "entity_id": created["id"],
        "created": created,
    }


@pytest.mark.smoke
def test_crm_refresh_capstone_seed_specialist_storage(tmp_path: Path) -> None:
    target = tmp_path / "crm-capstone"
    result = refresh_example_network("crm", root=target, register=False, yes=True)
    assert result.declined is False
    assert result.seed_bootstrap_count == 15
    assert_crm_seed_capstone(target)


@pytest.mark.smoke
def test_empty_crm_refresh_capstone_create_on_deliver_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "empty-crm-capstone"
    result = refresh_example_network("empty-crm", root=target, register=False, yes=True)
    assert result.declined is False
    assert result.seed_bootstrap_count == 0
    assert not (target / "seed.json").exists()
    demo_storage = target / "agents" / "demographic" / "storage.json"
    prof_storage = target / "agents" / "professional" / "storage.json"
    assert not demo_storage.exists()
    assert not prof_storage.exists()

    outcome = run_create_on_deliver(monkeypatch, target, PAUL_MURPHY_LOOKUP)
    created = outcome["created"]
    assert created["name"] == "Paul Murphy"
    assert created["employer"] == "Acme Corp"
    assert_bind_storage(entity_id=outcome["entity_id"], actor_kind="bind")

    demographic = json.loads(demo_storage.read_text(encoding="utf-8"))
    professional = json.loads(prof_storage.read_text(encoding="utf-8"))
    assert len(demographic.get("records", {})) == 1
    assert len(professional.get("records", {})) == 1

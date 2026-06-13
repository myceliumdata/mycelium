"""Tests for QueryResponse.provenance when EntityQuery.provenance=true."""

from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.context import reset_context_builder
from agents.dispatch import assemble_response_node
from agents.entity_resolution import lookup_entities_by_key
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.query_provenance import build_query_provenance
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery, MyceliumGraphState, QueryResponse
from mycelium_mcp.server import _neutral_json_schema
from network.paths import NetworkPaths
from network_helpers import import_seed_for_test
from storage.core import reset_storage
from versioned_storage_fixtures import versioned_found

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm" / "seed.json"


def _write_network_root(tmp_path: Path) -> None:
    shutil_categories = json.loads(SAMPLE_CATEGORIES.read_text(encoding="utf-8"))
    (tmp_path / "categories.json").write_text(
        json.dumps(shutil_categories),
        encoding="utf-8",
    )
    (tmp_path / "network.json").write_text(
        json.dumps(
            {
                "name": "crm",
                "mvr": {
                    "bind_fields": ["name", "employer"],
                },
            },
        ),
        encoding="utf-8",
    )
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps({"people": [{"name": "Paul Murphy", "employer": "Acme Corp"}]}),
        encoding="utf-8",
    )


def _configure_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    _write_network_root(tmp_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(tmp_path / "seed.json"))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(tmp_path / "categories.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    return str(tmp_path / "agent_data")


def _seed_entity_id() -> str:
    registry = get_entity_registry()
    matches = registry.lookup_by_name("Paul Murphy")
    assert matches
    return str(matches[0].id)


def _write_linkedin_storage(agent_data: Path, entity_id: str) -> dict:
    linkedin_entry = versioned_found(
        at="2026-06-11T12:00:00+00:00",
        value="https://linkedin.com/in/paul-murphy",
        category="social",
        specialist_name="social_specialist",
    )
    storage_dir = agent_data / "social"
    storage_dir.mkdir(parents=True, exist_ok=True)
    payload = {"records": {entity_id: {"linkedin": linkedin_entry}}}
    (storage_dir / "storage.json").write_text(json.dumps(payload), encoding="utf-8")
    return linkedin_entry


@pytest.fixture
def provenance_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()

    agent_data = _configure_env(tmp_path, monkeypatch)
    reset_category_tree()
    get_category_tree()
    import_seed_for_test(tmp_path / "seed.json")
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", agent_data)
    entity_id = _seed_entity_id()
    _write_linkedin_storage(Path(agent_data), entity_id)
    reset_core_graph()

    yield entity_id, agent_data

    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()


@pytest.mark.smoke
def test_build_query_provenance_reads_versioned_storage(
    provenance_env: tuple[str, str],
    tmp_path: Path,
) -> None:
    entity_id, agent_data = provenance_env
    paths = replace(
        NetworkPaths.from_root(tmp_path),
        agents_dir=Path(agent_data),
    )
    payload = build_query_provenance(
        entity_ids=[entity_id],
        requested_attributes=["linkedin"],
        paths=paths,
    )
    assert payload is not None
    entities = payload["entities"]
    assert len(entities) == 1
    assert entities[0]["id"] == entity_id
    linkedin = entities[0]["attributes"]["linkedin"]
    assert linkedin["current_version_id"] == "v1"
    assert len(linkedin["versions"]) == 1
    assert linkedin["versions"][0]["value"] == "https://linkedin.com/in/paul-murphy"


@pytest.mark.smoke
def test_build_query_provenance_skips_bind_fields(
    provenance_env: tuple[str, str],
    tmp_path: Path,
) -> None:
    entity_id, agent_data = provenance_env
    paths = replace(
        NetworkPaths.from_root(tmp_path),
        agents_dir=Path(agent_data),
    )
    payload = build_query_provenance(
        entity_ids=[entity_id],
        requested_attributes=["name", "employer", "linkedin"],
        paths=paths,
    )
    assert payload is not None
    attrs = payload["entities"][0]["attributes"]
    assert "name" not in attrs
    assert "employer" not in attrs
    assert "linkedin" in attrs


@pytest.mark.smoke
def test_assemble_response_attaches_provenance_when_requested(
    provenance_env: tuple[str, str],
) -> None:
    entity_id, _agent_data = provenance_env
    state = MyceliumGraphState(
        query=EntityQuery(
            entity_key="Paul Murphy",
            requested_attributes=["linkedin"],
            provenance=True,
        ),
        matched_records=[
            {
                "id": entity_id,
                "name": "Paul Murphy",
                "employer": "Acme Corp",
                "_registry": True,
                "_validation_state": "validated",
            },
        ],
        current_id=entity_id,
        entity_resolution_kind="exact",
        invocation_thread_id="prov-unit",
    )
    result = assemble_response_node(state)
    response = result["response"]
    assert response.outcome in {"assembled", "found"}
    assert response.provenance is not None
    linkedin = response.provenance["entities"][0]["attributes"]["linkedin"]
    assert linkedin["current_version_id"] == "v1"
    assert linkedin["versions"][0]["status"] == "found"


@pytest.mark.smoke
def test_assemble_response_omits_provenance_when_flag_false(
    provenance_env: tuple[str, str],
) -> None:
    entity_id, _agent_data = provenance_env
    state = MyceliumGraphState(
        query=EntityQuery(
            entity_key="Paul Murphy",
            requested_attributes=["linkedin"],
            provenance=False,
        ),
        matched_records=[
            {
                "id": entity_id,
                "name": "Paul Murphy",
                "employer": "Acme Corp",
                "_registry": True,
                "_validation_state": "validated",
            },
        ],
        current_id=entity_id,
        entity_resolution_kind="exact",
        invocation_thread_id="prov-unit",
    )
    result = assemble_response_node(state)
    response = result["response"]
    assert response.provenance is None


@pytest.mark.smoke
def test_run_query_with_provenance_flag(
    provenance_env: tuple[str, str],
) -> None:
    entity_id, _agent_data = provenance_env
    with_prov = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            requested_attributes=["linkedin"],
            provenance=True,
        ),
    )
    assert with_prov.outcome == "assembled"
    assert with_prov.provenance is not None
    assert with_prov.provenance["entities"][0]["id"] == entity_id

    without_prov = run_query(
        EntityQuery(
            entity_key="Paul Murphy",
            requested_attributes=["linkedin"],
            provenance=False,
        ),
    )
    assert without_prov.provenance is None


@pytest.mark.smoke
def test_build_query_provenance_multi_match_entities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_storage()
    reset_entity_registry()
    reset_category_tree()
    agent_data = _configure_env(tmp_path, monkeypatch)
    shutil.copy(EXAMPLE_CRM_SEED, tmp_path / "seed.json")
    reset_category_tree()
    get_category_tree()
    import_seed_for_test(tmp_path / "seed.json")
    matches = lookup_entities_by_key("Kevin Zhang")
    assert len(matches) == 2
    entity_ids = [str(match["id"]) for match in matches]
    agent_path = Path(agent_data)
    storage_dir = agent_path / "social"
    storage_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict] = {}
    for index, entity_id in enumerate(entity_ids):
        records[entity_id] = {
            "linkedin": versioned_found(
                at=f"2026-06-11T12:0{index}:00+00:00",
                value=f"https://linkedin.com/in/kevin-{index}",
                category="social",
                specialist_name="social_specialist",
            ),
        }
    (storage_dir / "storage.json").write_text(
        json.dumps({"records": records}),
        encoding="utf-8",
    )
    paths = replace(
        NetworkPaths.from_root(tmp_path),
        agents_dir=agent_path,
    )
    payload = build_query_provenance(
        entity_ids=entity_ids,
        requested_attributes=["linkedin"],
        paths=paths,
    )
    assert payload is not None
    assert len(payload["entities"]) == 2
    returned_ids = {item["id"] for item in payload["entities"]}
    assert returned_ids == set(entity_ids)


@pytest.mark.smoke
def test_query_response_schema_documents_provenance() -> None:
    schema = _neutral_json_schema(QueryResponse)
    props = schema.get("properties") or {}
    assert "provenance" in props
    description = schema.get("description") or ""
    assert "provenance" in description

"""Smoke tests for the mycelium-admin read-only HTTP daemon."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents.entity_registry import reset_entity_registry
from agents.entity_resolution import lookup_entities_by_key
from mycelium_admin.server import bootstrap_admin, create_app
from network_helpers import import_seed_for_test
from network.introspection import build_network_status, status_to_dict
from versioned_storage_fixtures import versioned_found
from network.paths import NO_NETWORK_CONFIGURED_MSG, NetworkPaths, apply_network_paths

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"


def _configure_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, root: Path) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    apply_network_paths(NetworkPaths.from_root(root))
    reset_entity_registry()


def _seed_only_root(tmp_path: Path) -> Path:
    root = tmp_path / "seed_only"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    shutil.copy(EXAMPLE_CRM / "network.json", root / "network.json")
    return root


def _ontology_root(tmp_path: Path) -> Path:
    root = tmp_path / "ontology_only"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    return root


def _metering_network_json() -> dict[str, object]:
    data = json.loads((EXAMPLE_CRM / "network.json").read_text(encoding="utf-8"))
    metering = dict(data.get("metering") or {})
    metering["enabled"] = True
    metering["payment"] = {
        "enabled": False,
        "provider": "mock",
        "require_paid_before_accept": True,
    }
    data["metering"] = metering
    return data


def _populated_root(tmp_path: Path) -> Path:
    root = tmp_path / "populated"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    shutil.copy(EXAMPLE_CRM / "network.json", root / "network.json")
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    (root / "agent_registry.json").write_text(
        json.dumps(
            {
                "version": "1.0",
                "last_updated": "2026-06-03T00:00:00+00:00",
                "agents": {
                    "contact_specialist": {
                        "name": "contact_specialist",
                        "category": "contact",
                        "description": "Contact specialist",
                        "module_path": "dyn",
                        "entrypoint": "run",
                        "is_generated": True,
                    },
                },
            },
        ),
        encoding="utf-8",
    )
    return root


def _metering_root(tmp_path: Path) -> Path:
    root = tmp_path / "metering"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    (root / "network.json").write_text(
        json.dumps(_metering_network_json(), indent=2),
        encoding="utf-8",
    )
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    (root / "agent_registry.json").write_text(
        json.dumps(
            {
                "version": "1.0",
                "last_updated": "2026-06-03T00:00:00+00:00",
                "agents": {
                    "contact_specialist": {
                        "name": "contact_specialist",
                        "category": "contact",
                        "description": "Contact specialist",
                        "module_path": "dyn",
                        "entrypoint": "run",
                        "is_generated": True,
                    },
                },
            },
        ),
        encoding="utf-8",
    )
    return root


def _client_for_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    root: Path,
) -> TestClient:
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    _configure_root(monkeypatch, tmp_path, root)
    if (root / "seed.json").is_file():
        import_seed_for_test(root / "seed.json")
    bootstrap_admin()
    return TestClient(create_app())


@pytest.mark.smoke
def test_health_returns_network_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["network_root"] == str(root.resolve())
    assert payload["network_name"] == "crm"


@pytest.mark.smoke
def test_status_json_matches_introspection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    response = client.get("/status")

    assert response.status_code == 200
    expected = status_to_dict(build_network_status())
    assert response.json() == expected
    assert response.json()["registry_entity_count"] == 15
    assert response.json()["ontology_present"] is True


@pytest.mark.smoke
def test_status_entity_drill_down(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _populated_root(tmp_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    apply_network_paths(NetworkPaths.from_root(root))
    import_seed_for_test(root / "seed.json")
    person_id = lookup_entities_by_key("Andrea Kalmans")[0]["id"]
    agents_dir = root / "agents" / "contact"
    agents_dir.mkdir(parents=True)
    (agents_dir / "storage.json").write_text(
        json.dumps(
            {
                "version": "1.0",
                "records": {
                    person_id: {
                        "email": versioned_found(
                            at="2026-06-11T05:00:00+00:00",
                            value="akalmans@example.com",
                        ),
                    },
                },
            },
        ),
        encoding="utf-8",
    )
    client = _client_for_root(monkeypatch, tmp_path, root)
    entity = "Andrea Kalmans"

    response = client.get("/status", params={"entity": entity})

    assert response.status_code == 200
    payload = response.json()
    assert payload["entity_key"] == entity
    assert payload["entity_matches"] == 1
    fields = payload["entity_fields"]
    email = next(item for item in fields if item["field"] == "email")
    assert email["field_kind"] == "extended"
    assert email["status"] == "found"
    assert email["value"] == "akalmans@example.com"
    assert email["versions"]
    assert email["versions"][0]["id"] == "v1"
    bind_fields = [item for item in fields if item["field_kind"] == "bind"]
    assert {item["field"] for item in bind_fields} == {"name", "employer"}


@pytest.mark.smoke
def test_status_reflects_entities_change_without_restart(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    first = client.get("/status")
    assert first.status_code == 200
    assert first.json()["registry_entity_count"] == 15

    (root / "entities.json").write_text(
        json.dumps(
            {
                "version": "1.0",
                "last_updated": "2026-06-10T12:00:00+00:00",
                "entities": {
                    "solo-id": {
                        "id": "solo-id",
                        "name": "Solo Person",
                        "employer": "Test Co",
                        "validation_state": "validated",
                        "field_states": {
                            "name": "validated",
                            "employer": "validated",
                        },
                        "attr_sources": {},
                        "last_researched_at": {},
                        "source": "seed_bootstrap",
                        "created_at": "2026-06-10T12:00:00+00:00",
                    },
                },
                "bind_index": {"solo person|test co": "solo-id"},
            },
        ),
        encoding="utf-8",
    )

    second = client.get("/status")
    assert second.status_code == 200
    assert second.json()["registry_entity_count"] == 1


@pytest.mark.smoke
def test_status_category_filter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _ontology_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    response = client.get("/status", params={"category": "contact"})

    assert response.status_code == 200
    categories = response.json()["categories"]
    assert categories
    assert all(item["name"] == "contact" for item in categories)


@pytest.mark.smoke
def test_capabilities_has_ontology_and_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _ontology_root(tmp_path)
    shutil.copy(EXAMPLE_CRM / "guide.md", root / "guide.md")
    client = _client_for_root(monkeypatch, tmp_path, root)

    response = client.get("/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert "ontology" in payload
    assert "policy" in payload
    assert payload["ontology"]["present"] is True
    assert payload["policy"]["query"]["tool"] == "query_entity"


@pytest.mark.smoke
def test_bootstrap_fails_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.delenv("MYCELIUM_NETWORK_ROOT", raising=False)
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setattr("mycelium_admin.server.load_dotenv", lambda *a, **k: None)

    with pytest.raises(ValueError, match=NO_NETWORK_CONFIGURED_MSG.split(".")[0]):
        bootstrap_admin()


@pytest.mark.smoke
def test_serves_admin_ui_when_dist_present(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    framework = tmp_path / "framework"
    dist = framework / "admin-ui" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!DOCTYPE html><html><body>admin ui</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr("network.paths.framework_root", lambda: framework)

    root = _populated_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    html = client.get("/")
    assert html.status_code == 200
    assert "admin ui" in html.text

    status = client.get("/status")
    assert status.status_code == 200
    assert status.json()["registry_entity_count"] == 15


@pytest.mark.smoke
def test_admin_module_forces_sync_checkpointer() -> None:
    """Admin daemon must compile the graph with sync SqliteSaver (see server.py)."""
    import mycelium_admin.server as admin_server  # noqa: F401 — sets env before graphs.core
    from graphs.core import get_core_graph, reset_core_graph

    assert admin_server.os.environ.get("MYCELIUM_USE_SYNC_CHECKPOINTER") == "1"
    reset_core_graph()
    get_core_graph()
    import graphs.core as core

    assert core._is_async_checkpointer is False


@pytest.mark.smoke
def test_admin_query_seed_entity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """POST /query exercises run_query; requires sync checkpointer in admin process."""
    root = _populated_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)
    monkeypatch.setattr(
        "tools.research.is_research_available",
        lambda: False,
    )

    response = client.post(
        "/query",
        json={"lookup": {"name": "Andrea Kalmans", "employer": "Lontra Ventures"}},
    )

    assert response.status_code == 200
    step1 = response.json()
    assert step1["outcome"] == "lookup_resolved"
    delivery_id = step1["delivery"]["delivery_id"]

    deliver = client.post("/query", json={"delivery_id": delivery_id})
    assert deliver.status_code == 200
    payload = deliver.json()
    assert payload["outcome"] in {"found", "assembled"}
    assert payload["results"]


@pytest.mark.smoke
def test_admin_query_registry_bind(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """POST /query create-on-deliver via full MVR lookup (Paul Murphy not in seed)."""
    root = _populated_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)
    monkeypatch.setattr(
        "tools.research.is_research_available",
        lambda: False,
    )

    step1 = client.post(
        "/query",
        json={
            "lookup": {"name": "Paul Murphy", "employer": "Acme Corp"},
            "requested_attributes": ["email"],
        },
    )
    assert step1.status_code == 200
    resolved = step1.json()
    assert resolved["outcome"] == "lookup_resolved"
    assert resolved["total_matches"] == 0
    delivery_id = resolved["delivery"]["delivery_id"]

    deliver = client.post("/query", json={"delivery_id": delivery_id})
    assert deliver.status_code == 200
    payload = deliver.json()
    assert payload["outcome"] in {"found", "assembled"}
    assert payload["results"]


@pytest.mark.smoke
def test_admin_query_identity_bind_without_attrs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Full MVR lookup with no attrs issues delivery; step 2 creates provisional row."""
    root = _populated_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    step1 = client.post(
        "/query",
        json={
            "lookup": {"name": "Paul Murphy", "employer": "Ormi Labs"},
        },
    )
    assert step1.status_code == 200
    resolved = step1.json()
    assert resolved["outcome"] == "lookup_resolved"
    assert resolved["total_matches"] == 0
    assert resolved["delivery"]["create_on_deliver"] is True
    assert "step 2 will create" in resolved["message"]
    delivery_id = resolved["delivery"]["delivery_id"]

    deliver = client.post("/query", json={"delivery_id": delivery_id})
    assert deliver.status_code == 200
    payload = deliver.json()
    assert payload["outcome"] == "found"
    assert payload["results"]
    assert payload["results"][0]["name"] == "Paul Murphy"
    assert payload["results"][0]["employer"] == "Ormi Labs"


@pytest.mark.smoke
def test_admin_query_existing_match_omits_create_on_deliver(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Step-1 JSON for an existing registry row omits delivery.create_on_deliver."""
    root = _populated_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    response = client.post(
        "/query",
        json={"lookup": {"name": "Nichanan Kesonpat"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "lookup_resolved"
    assert payload["total_matches"] >= 1
    assert "create_on_deliver" not in payload.get("delivery", {})
    assert "registry match" in payload["message"]
    assert "step 2" in payload["message"]


@pytest.mark.smoke
def test_admin_query_step1_wire_json_shape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Admin POST /query returns client-visible JSON (public_dict), not model_dump."""
    root = _populated_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    create = client.post(
        "/query",
        json={"lookup": {"name": "Road Runner", "employer": "Acme Corp"}},
    )
    assert create.status_code == 200
    create_payload = create.json()
    assert create_payload["outcome"] == "lookup_resolved"
    assert create_payload["total_matches"] == 0
    assert create_payload["delivery"]["create_on_deliver"] is True
    assert "step 2 will create" in create_payload["message"]
    assert "quote" in create_payload
    assert create_payload["quote"] is None

    existing = client.post(
        "/query",
        json={
            "lookup": {
                "name": "Nichanan Kesonpat",
                "employer": "1k(x)",
            },
        },
    )
    assert existing.status_code == 200
    existing_payload = existing.json()
    assert existing_payload["outcome"] == "lookup_resolved"
    assert existing_payload["total_matches"] == 1
    assert "create_on_deliver" not in existing_payload["delivery"]
    assert existing_payload["delivery"].get("create_on_deliver") is not False
    assert "1 registry match" in existing_payload["message"]
    assert "quote" in existing_payload
    assert existing_payload["quote"] is None


@pytest.mark.smoke
def test_admin_query_passes_quote_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from datetime import datetime, timezone
    from typing import Any

    from agents.classification import get_category_tree, reset_category_tree
    from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
    from agents.registry import reset_agent_registry
    from graphs.core import reset_core_graph
    from tools.research import ResearchRunResult

    root = _metering_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    reset_category_tree()
    get_category_tree()
    reset_agent_registry()
    reset_agent_factory()
    get_agent_factory().create_specialist(
        "contact",
        "contact_specialist",
        "Direct contact info",
        examples=["email", "phone"],
        auto_commit=False,
    )
    reset_core_graph()

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

    client.post(
        "/query",
        json={
            "lookup": {"name": "Paul Murphy", "employer": "Acme Corp"},
        },
    )
    quoted = client.post(
        "/query",
        json={
            "lookup": {"name": "Paul Murphy", "employer": "Acme Corp"},
            "requested_attributes": ["email"],
        },
    )
    assert quoted.status_code == 200
    quote_payload = quoted.json()
    assert quote_payload["outcome"] == "quote_required"
    quote_id = quote_payload["quote"]["quote_id"]
    delivery_id = quote_payload["delivery"]["delivery_id"]

    accepted = client.post(
        "/query",
        json={
            "delivery_id": delivery_id,
            "quote_id": quote_id,
        },
    )
    assert accepted.status_code == 200
    assert accepted.json()["outcome"] == "assembled"


@pytest.mark.smoke
def test_health_503_when_not_bootstrapped() -> None:
    import mycelium_admin.server as admin_server

    saved = admin_server._NETWORK_INFO
    admin_server._NETWORK_INFO = None
    try:
        client = TestClient(create_app())
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["status"] == "error"
    finally:
        admin_server._NETWORK_INFO = saved

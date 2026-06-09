"""Smoke tests for the mycelium-admin read-only HTTP daemon."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents.seed import find_by_key, reset_seed_data
from mycelium_admin.server import bootstrap_admin, create_app
from network.introspection import build_network_status, status_to_dict
from network.paths import NO_NETWORK_CONFIGURED_MSG, NetworkPaths, apply_network_paths

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"


def _configure_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, root: Path) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    apply_network_paths(NetworkPaths.from_root(root))
    reset_seed_data()


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


def _client_for_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    root: Path,
) -> TestClient:
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    _configure_root(monkeypatch, tmp_path, root)
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
    assert response.json()["seed_people_count"] == 15
    assert response.json()["ontology_present"] is False


@pytest.mark.smoke
def test_status_entity_drill_down(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _populated_root(tmp_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    apply_network_paths(NetworkPaths.from_root(root))
    reset_seed_data()
    person_id = find_by_key("Andrea Kalmans")[0]["id"]
    agents_dir = root / "agents" / "contact"
    agents_dir.mkdir(parents=True)
    (agents_dir / "storage.json").write_text(
        json.dumps(
            {
                "version": "1.0",
                "records": {
                    person_id: {
                        "email": {
                            "status": "found",
                            "value": "akalmans@example.com",
                        },
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
    bind_fields = [item for item in fields if item["field_kind"] == "bind"]
    assert {item["field"] for item in bind_fields} == {"name", "employer"}


@pytest.mark.smoke
def test_status_reflects_seed_change_without_restart(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)

    first = client.get("/status")
    assert first.status_code == 200
    assert first.json()["seed_people_count"] == 15

    (root / "seed.json").write_text(
        json.dumps({"people": [{"name": "Solo Person", "employer": "Test Co"}]}),
        encoding="utf-8",
    )

    second = client.get("/status")
    assert second.status_code == 200
    assert second.json()["seed_people_count"] == 1


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
    assert status.json()["seed_people_count"] == 15


@pytest.mark.smoke
def test_admin_query_seed_entity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _populated_root(tmp_path)
    client = _client_for_root(monkeypatch, tmp_path, root)
    monkeypatch.setattr(
        "tools.research.is_research_available",
        lambda: False,
    )

    response = client.post(
        "/query",
        json={"entity_key": "Andrea Kalmans"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] in {"found", "assembled"}
    assert payload["results"]


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

"""Smoke and full tests for ``mycelium network status``."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.entity_resolution import lookup_entities_by_key
from network_helpers import import_seed_for_test
from network.introspection import (
    build_network_status,
    format_category_examples,
    format_status_demo,
    format_status_verbose,
    status_to_dict,
)
from network.paths import NetworkPaths, apply_network_paths
from versioned_storage_fixtures import versioned_found, versioned_pending

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


@pytest.mark.smoke
def test_format_category_examples_unit() -> None:
    assert format_category_examples("contact", []) == "contact"
    assert format_category_examples("contact", ["email"]) == "contact (e.g., email)"
    assert (
        format_category_examples("contact", ["email", "phone"])
        == "contact (e.g., email, phone)"
    )
    assert (
        format_category_examples("contact", ["email", "phone", "mobile"])
        == "contact (e.g., email, phone, …)"
    )


@pytest.mark.smoke
def test_status_demo_entities_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    import_seed_for_test(root / "seed.json")

    text = format_status_demo(build_network_status())
    assert "Entities: ✅ (15)" in text
    assert "Current ontology:" in text
    assert "contact (e.g., email, phone, …)" in text
    assert "Existing specialists:" in text
    assert "demographic (15)" in text
    assert "professional (15)" in text
    assert "Root:" not in text


@pytest.mark.smoke
def test_status_demo_ontology_without_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _ontology_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)

    text = format_status_demo(build_network_status())
    assert "Current ontology:" in text
    assert "contact (e.g., email, phone, …)" in text
    assert "Existing specialists: ❌" in text
    assert "contact_specialist" not in text


@pytest.mark.smoke
def test_status_demo_contact_has_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "populated"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    _configure_root(monkeypatch, tmp_path, root)
    import_seed_for_test(root / "seed.json")
    person_id = lookup_entities_by_key("Andrea Kalmans")[0]["id"]
    agents_dir = root / "agents" / "contact"
    agents_dir.mkdir(parents=True)
    (agents_dir / "storage.json").write_text(
        json.dumps({"version": "1.0", "records": {person_id: {"email": "a@b.com"}}}),
        encoding="utf-8",
    )

    text = format_status_demo(build_network_status())
    assert "Existing specialists:" in text
    assert "contact (1)" in text
    assert "contact_specialist" not in text


@pytest.mark.smoke
def test_status_verbose_has_root_and_agents(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _ontology_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)

    text = format_status_verbose(build_network_status())
    assert "Root:" in text
    assert "contact: agent=contact_specialist" in text


@pytest.mark.smoke
def test_status_empty_network_entities_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    import_seed_for_test(root / "seed.json")

    summary = build_network_status()
    assert summary.registry_entity_count == 15
    assert summary.ontology_present is True
    assert len(summary.categories) == 6
    seeded = {item.category for item in summary.specialists if item.record_count > 0}
    assert seeded == {"demographic", "professional"}


@pytest.mark.smoke
def test_status_populated_network_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
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
    _configure_root(monkeypatch, tmp_path, root)
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
                            at="2026-06-10T12:00:00+00:00",
                            value="akalmans@example.com",
                        ),
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    summary = build_network_status()
    assert summary.ontology_present is True
    assert len(summary.categories) == 6
    assert summary.categories[0].examples
    contact = next(item for item in summary.specialists if item.category == "contact")
    assert contact.record_count == 1


@pytest.mark.smoke
def test_status_json_round_trip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    import_seed_for_test(root / "seed.json")

    payload = status_to_dict(build_network_status())
    assert payload["registry_entity_count"] == 15
    assert payload["ontology_present"] is True
    assert isinstance(payload["specialists"], list)
    seeded = {item["category"] for item in payload["specialists"] if item["record_count"] > 0}
    assert seeded == {"demographic", "professional"}


@pytest.mark.smoke
def test_status_cli_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    import_seed_for_test(root / "seed.json")
    env = {
        **os.environ,
        "MYCELIUM_NETWORKS_CONFIG": str(tmp_path / "missing.json"),
        "LANGCHAIN_TRACING_V2": "false",
        "NO_COLOR": "1",
        "PYTHONPATH": str(REPO_ROOT / "src"),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "main",
            "network",
            "status",
            "--network-dir",
            str(root),
            "--json",
        ],
        cwd=REPO_ROOT / "src",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["registry_entity_count"] == 15


@pytest.mark.smoke
def test_status_cli_verbose(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    env = {
        **os.environ,
        "MYCELIUM_NETWORKS_CONFIG": str(tmp_path / "missing.json"),
        "LANGCHAIN_TRACING_V2": "false",
        "NO_COLOR": "1",
        "PYTHONPATH": str(REPO_ROOT / "src"),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "main",
            "network",
            "status",
            "--network-dir",
            str(root),
            "--verbose",
        ],
        cwd=REPO_ROOT / "src",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "Root:" in result.stdout


@pytest.mark.smoke
def test_status_registry_entity_lookup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _ontology_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    registry = get_entity_registry()
    entity, _created = registry.bind_provisional("New Person", "Acme Labs")
    registry.promote_validated(entity.id)
    registry.record_research_attribution(
        entity.id,
        {"email": ("contact", "2026-06-09T12:00:00+00:00")},
    )

    summary = build_network_status(entity_key=entity.id)
    assert summary.entity_matches == 1
    assert summary.entity_resolution_kind == "exact"
    assert summary.entity_match_summaries[0].source == "registry"
    assert summary.entity_match_summaries[0].validation_state == "validated"
    assert summary.entity_match_summaries[0].research_allowed is True
    bind_fields = [item for item in summary.entity_fields if item.field_kind == "bind"]
    assert {item.field for item in bind_fields} == {"name", "employer"}
    extended = [item for item in summary.entity_fields if item.field_kind == "extended"]
    if extended:
        email = next((item for item in extended if item.field == "email"), None)
        if email is not None:
            assert email.attr_source == "contact"


@pytest.mark.smoke
def test_status_near_miss_suggestions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    import_seed_for_test(root / "seed.json")

    summary = build_network_status(entity_key="Andrea Kalman")
    assert summary.entity_resolution_kind == "suggest"
    assert summary.entity_matches == 0
    assert summary.entity_suggestions
    assert summary.entity_suggestions[0]["entity_key"]


@pytest.mark.full
def test_status_person_drill_down(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "populated"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    _configure_root(monkeypatch, tmp_path, root)
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
                        "email": versioned_pending(
                            started_at="2026-06-10T12:00:00+00:00",
                        ),
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    summary = build_network_status(entity_key="Andrea Kalmans", category_filter="contact")
    demo = format_status_demo(summary)
    assert "Entity lookup:" in demo
    assert "email (contact/contact_specialist): pending" in demo
    assert summary.entity_matches == 1


@pytest.mark.smoke
def test_status_entity_fields_include_versions_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "populated"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
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
    _configure_root(monkeypatch, tmp_path, root)
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

    payload = status_to_dict(build_network_status(entity_key="Andrea Kalmans"))
    email = next(
        item for item in payload["entity_fields"] if item["field"] == "email"
    )
    assert email["status"] == "found"
    assert email["versions"]
    assert email["versions"][0]["id"] == "v1"
    assert email["versions"][0]["value"] == "akalmans@example.com"
    bind_rows = [item for item in payload["entity_fields"] if item["field_kind"] == "bind"]
    assert bind_rows
    assert all(item.get("versions") for item in bind_rows)


@pytest.mark.smoke
def test_status_flat_v1_field_fails_loud_on_drill_down(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "flat-v1"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
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
    _configure_root(monkeypatch, tmp_path, root)
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
                        "email": {
                            "status": "found",
                            "value": "legacy@example.com",
                            "researched_at": "2026-06-01T00:00:00+00:00",
                        },
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="deprecated flat field format"):
        build_network_status(entity_key="Andrea Kalmans")

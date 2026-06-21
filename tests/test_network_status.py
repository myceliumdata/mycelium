"""Smoke and full tests for ``mycelium network status``."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agents.attribute_write import bind_provisional
from agents.entity_registry import RegistryEntity, get_entity_registry, reset_entity_registry
from registry_helpers import lookup_entities_by_name as lookup_entities_by_key
from network_helpers import copy_crm_network_manifest, import_seed_for_test
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
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm-seeded"
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"


def _configure_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, root: Path) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    if not (root / "network.json").is_file():
        copy_crm_network_manifest(root)
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
    copy_crm_network_manifest(root)
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
    assert "entity_key" not in payload
    seeded = {item["category"] for item in payload["specialists"] if item["record_count"] > 0}
    assert seeded == {"demographic", "professional"}


@pytest.mark.smoke
def test_status_json_omits_entity_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    import_seed_for_test(root / "seed.json")

    overview = status_to_dict(build_network_status())
    assert "entity_key" not in overview

    drill = status_to_dict(
        build_network_status(resolve_lookup={"name": "Andrea Kalmans"}),
    )
    assert "entity_key" not in drill
    assert drill["resolve"]["lookup"] == {"name": "Andrea Kalmans"}


@pytest.mark.smoke
def test_status_cli_lookup_json(
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
            "--lookup-json",
            json.dumps({"name": "Andrea Kalmans", "employer": "Lontra Ventures"}),
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
    assert payload["resolve_matches"] == 1
    assert payload["resolve"]["lookup"] == {
        "name": "Andrea Kalmans",
        "employer": "Lontra Ventures",
    }
    assert "entity_key" not in payload


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
def test_status_bind_rows_include_empty_employer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Regression: status lists every MVR bind row even when employer is absent.

    Uses a synthetic registry row (direct ``bind_values`` without employer) because
    bind_index operations require full MVR (Program 3 polish P4). Guards status
    display of missing bind fields, not a production bind scenario.
    """
    root = tmp_path / "empty_employer"
    root.mkdir()
    shutil.copy(EXAMPLE_CRM / "seed.json", root / "seed.json")
    shutil.copy(SAMPLE_CATEGORIES, root / "categories.json")
    _configure_root(monkeypatch, tmp_path, root)
    registry = get_entity_registry()
    entity_id = str(uuid.uuid4())
    entity = RegistryEntity(
        id=entity_id,
        bind_values={"name": "Solo Name"},
        validation_state="validated",
        source="test_fixture",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    registry.register_entity(entity)
    registry.save_entity(entity)

    summary = build_network_status(resolve_id=entity_id)
    employer = next(
        item for item in summary.entity_fields if item.field == "employer"
    )
    assert employer.field_kind == "bind"
    assert employer.value is None


@pytest.mark.smoke
def test_status_registry_entity_lookup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _ontology_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    registry = get_entity_registry()
    entity, _created = bind_provisional("New Person", "Acme Labs", registry=registry)
    registry.promote_validated(entity.id)
    registry.record_research_attribution(
        entity.id,
        {"email": ("contact", "2026-06-09T12:00:00+00:00")},
    )

    summary = build_network_status(resolve_id=entity.id)
    assert summary.resolve_matches == 1
    assert summary.resolve_kind == "exact"
    assert summary.resolve_match_summaries[0].source == "registry"
    assert summary.resolve_match_summaries[0].validation_state == "validated"
    assert summary.resolve_match_summaries[0].research_allowed is True
    bind_fields = [item for item in summary.entity_fields if item.field_kind == "bind"]
    assert {item.field for item in bind_fields} == {"name", "employer"}
    extended = [item for item in summary.entity_fields if item.field_kind == "extended"]
    if extended:
        email = next((item for item in extended if item.field == "email"), None)
        if email is not None:
            assert email.attr_source == "contact"


@pytest.mark.smoke
def test_status_exact_inspect_no_fuzzy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Inspect uses exact lookup only — no fuzzy suggestion ranking."""
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)
    import_seed_for_test(root / "seed.json")

    summary = build_network_status(resolve_lookup={"name": "Andrea Kalman"})
    assert summary.resolve_kind == "none"
    assert summary.resolve_matches == 0
    assert summary.resolve_suggestions == []
    assert summary.resolve is not None
    assert summary.resolve.lookup == {"name": "Andrea Kalman"}


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

    summary = build_network_status(
        resolve_lookup={"name": "Andrea Kalmans"},
        category_filter="contact",
    )
    demo = format_status_demo(summary)
    assert "Resolve:" in demo
    assert "email (contact/contact_specialist): pending" in demo
    assert summary.resolve_matches == 1


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

    payload = status_to_dict(
        build_network_status(resolve_lookup={"name": "Andrea Kalmans"}),
    )
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
        build_network_status(resolve_lookup={"name": "Andrea Kalmans"})

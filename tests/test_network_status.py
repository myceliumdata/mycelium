"""Smoke and full tests for ``mycelium network status``."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agents.seed import find_by_key, reset_seed_data
from network.introspection import (
    build_network_status,
    format_category_examples,
    format_status_demo,
    format_status_verbose,
    status_to_dict,
)
from network.paths import NetworkPaths, apply_network_paths

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
def test_status_demo_seed_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)

    text = format_status_demo(build_network_status())
    assert "Seed: ✅ (15)" in text
    assert "Current ontology: ❌" in text
    assert "Existing specialists: ❌" in text
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
    person_id = find_by_key("Andrea Kalmans")[0]["id"]
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
def test_status_empty_network_seed_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _seed_only_root(tmp_path)
    _configure_root(monkeypatch, tmp_path, root)

    summary = build_network_status()
    assert summary.seed_people_count == 15
    assert summary.ontology_present is False
    assert summary.specialists == []


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

    payload = status_to_dict(build_network_status())
    assert payload["seed_people_count"] == 15
    assert payload["ontology_present"] is False
    assert isinstance(payload["specialists"], list)


@pytest.mark.smoke
def test_status_cli_json(
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
    assert payload["seed_people_count"] == 15


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
    person_id = find_by_key("Andrea Kalmans")[0]["id"]
    agents_dir = root / "agents" / "contact"
    agents_dir.mkdir(parents=True)
    (agents_dir / "storage.json").write_text(
        json.dumps(
            {
                "version": "1.0",
                "records": {person_id: {"email": {"status": "pending"}}},
            },
        ),
        encoding="utf-8",
    )

    summary = build_network_status(person_key="Andrea Kalmans", category_filter="contact")
    demo = format_status_demo(summary)
    assert "Person lookup:" in demo
    assert "email (contact/contact_specialist): pending" in demo
    assert summary.person_matches == 1

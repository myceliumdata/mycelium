"""Shared helpers for network path isolation in tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CRM_NETWORK_MANIFEST = REPO_ROOT / "examples" / "networks" / "crm" / "network.json"

NETWORK_PATH_ENV_KEYS = (
    "MYCELIUM_NETWORK_ROOT",
    "MYCELIUM_SEED_PATH",
    "MYCELIUM_ENTITIES_PATH",
    "MYCELIUM_AGENT_REGISTRY_PATH",
    "MYCELIUM_CATEGORIES_PATH",
    "MYCELIUM_AGENT_DATA_DIR",
    "MYCELIUM_SPECIALISTS_DIR",
    "MYCELIUM_CHECKPOINT_PATH",
    "MYCELIUM_DB_PATH",
)


def copy_crm_network_manifest(root: Path) -> Path:
    """Copy committed CRM ``network.json`` (full ``mvr.grains`` + ``metering``)."""
    root.mkdir(parents=True, exist_ok=True)
    dest = root / "network.json"
    shutil.copy(CRM_NETWORK_MANIFEST, dest)
    return dest


def write_metering_network_json(
    path: Path,
    *,
    enabled: bool = True,
    **overrides: Any,
) -> None:
    """Write CRM-shaped manifest with optional ``metering`` overrides."""
    data = json.loads(CRM_NETWORK_MANIFEST.read_text(encoding="utf-8"))
    metering = dict(data.get("metering") or {})
    metering["enabled"] = enabled
    metering.update(overrides)
    data["metering"] = metering
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def crm_person_entities_path(root: Path) -> Path:
    """Canonical default-grain entity store path for CRM manifests."""
    return root / "entities" / "person.json"


def clear_network_path_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop path vars set by apply_network_paths (not tracked by monkeypatch undo)."""
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    for key in NETWORK_PATH_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def import_seed_for_test(
    seed_path: Path | None = None,
    *,
    tmp_path: Path | None = None,
    monkeypatch: pytest.MonkeyPatch | None = None,
    seed_src: Path | None = None,
) -> int:
    """Import ``seed.json`` into ``entities.json`` after ``MYCELIUM_*`` env is set.

    Simulates the **seed-import / refresh bootstrap** path: calls
    ``ensure_categories_for_mvr_bind`` before ``import_seed_file`` (which delegates
    to the default seed handler; full orchestration is ``run_network_bootstrap``).
    Do not use
    in create-on-deliver or empty-crm cold-start tests unless that path is under test.

    When ``seed_src`` and ``tmp_path`` are given, copies the file to
    ``tmp_path/seed.json``, sets network path env vars, then imports.
    Otherwise ``seed_path`` must already be configured via env.
    """
    from agents.entity_registry import reset_entity_registry
    from network.seed_import import import_seed_file

    if seed_src is not None:
        if tmp_path is None:
            msg = "tmp_path required when seed_src is provided"
            raise ValueError(msg)
        dest = tmp_path / "seed.json"
        shutil.copy(seed_src, dest)
        if not (tmp_path / "network.json").is_file() and CRM_NETWORK_MANIFEST.is_file():
            copy_crm_network_manifest(tmp_path)
        if monkeypatch is not None:
            monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
            monkeypatch.setenv("MYCELIUM_SEED_PATH", str(dest))
        seed_path = dest
    if seed_path is None:
        msg = "seed_path or (tmp_path, seed_src) required"
        raise ValueError(msg)

    from network.category_mvr_bootstrap import ensure_categories_for_mvr_bind
    from network.paths import NetworkPaths, apply_network_paths

    root = seed_path.parent
    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)
    ensure_categories_for_mvr_bind(paths)
    if monkeypatch is not None:
        monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(root / "agent_data"))
        (root / "agent_data").mkdir(parents=True, exist_ok=True)

    reset_entity_registry()
    return import_seed_file(seed_path)


def import_seed_at_root(root: Path) -> int:
    """Import ``root/seed.json`` when present (uses ``apply_network_paths``).

    Simulates **refresh-example-network** seed bootstrap (includes MVR category merge).
    """
    from agents.entity_registry import reset_entity_registry
    from network.paths import NetworkPaths, apply_network_paths
    from network.seed_import import import_seed_file

    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)
    from network.category_mvr_bootstrap import ensure_categories_for_mvr_bind

    ensure_categories_for_mvr_bind(paths)
    reset_entity_registry()
    return import_seed_file(paths.seed_path)


def apply_network_paths_monkeypatch(
    paths: Path | object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mirror ``NetworkPaths`` into pytest monkeypatch only (no ``os.environ`` leak)."""
    from network.paths import NetworkPaths, runtime_env_field_names

    if not isinstance(paths, NetworkPaths):
        msg = "paths must be a NetworkPaths instance"
        raise TypeError(msg)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(paths.root))
    for env_var, field in runtime_env_field_names().items():
        monkeypatch.setenv(env_var, str(getattr(paths, field)))


def mock_email_research(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    """Stub contact email research for fast batch-deliver smoke tests."""
    from datetime import datetime, timezone

    from tools.research import ResearchRunResult
    from versioned_storage_fixtures import versioned_found

    calls: dict[str, list[str]] = {}

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        llm: object | None = None,
    ) -> ResearchRunResult:
        _ = category, specialist_name, context, llm
        calls.setdefault(person_id, []).extend(target_fields)
        from agents.specialists.base import SpecialistStorage

        storage = SpecialistStorage(category=category)
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        for field in target_fields:
            rec[field] = versioned_found(
                at=now,
                value=f"{person_id[:8]}@batch.example",
                confidence=0.9,
                sources=[f"https://example.com/{person_id[:8]}"],
                category="contact",
                specialist_name="contact_specialist",
            )
        storage.save(data)
        return ResearchRunResult(fields_updated=list(target_fields), tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)
    return calls


def register_contact_specialist() -> None:
    """Register CRM contact specialist (required for email deliver smoke paths)."""
    from agents.factory.agent_factory import get_agent_factory

    get_agent_factory().create_specialist(
        "contact",
        "contact_specialist",
        "Direct contact info",
        examples=["email", "phone"],
        auto_commit=False,
    )

"""Smoke tests for formal network bootstrap phase."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.entity_registry import get_entity_registry, reset_entity_registry
from network.bootstrap import run_network_bootstrap
from network.bootstrap.handlers.default_seed import import_seed_rows, load_seed_people
from network.category_mvr_bootstrap import ensure_categories_for_mvr_bind
from network.paths import NetworkPaths, apply_network_paths
from network.seed_import import bootstrap_seed_at_paths, count_seed_rows, import_seed_file

REPO_ROOT = Path(__file__).resolve().parent.parent
CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm" / "seed.json"


def _prepare_root(tmp_path: Path, *, seed_src: Path | None = None) -> NetworkPaths:
    root = tmp_path / "net"
    root.mkdir(parents=True, exist_ok=True)
    if seed_src is not None:
        shutil.copy(seed_src, root / "seed.json")
    shutil.copy(
        REPO_ROOT / "examples" / "networks" / "crm" / "network.json",
        root / "network.json",
    )
    return NetworkPaths.from_root(root)


@pytest.mark.smoke
def test_run_network_bootstrap_crm_seed(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    result = run_network_bootstrap(paths)
    assert result.handler_id == "default_seed"
    assert result.entities_committed == 15
    assert result.sources_processed == ["seed.json"]
    assert not result.errors
    payload = json.loads(paths.entities_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 15
    assert len(payload["bind_index"]) == 15


@pytest.mark.smoke
def test_run_network_bootstrap_missing_seed(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path)
    result = run_network_bootstrap(paths)
    assert result.entities_committed == 0
    assert result.sources_processed == []


@pytest.mark.smoke
def test_load_seed_people_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "seed.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid seed JSON"):
        load_seed_people(bad)


@pytest.mark.smoke
def test_import_seed_rows_missing_employer(tmp_path: Path) -> None:
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps({"people": [{"name": "Ada Lovelace"}]}),
        encoding="utf-8",
    )
    apply_network_paths(NetworkPaths.from_root(tmp_path))
    ensure_categories_for_mvr_bind(NetworkPaths.from_root(tmp_path))
    reset_entity_registry()
    with pytest.raises(ValueError, match="missing employer"):
        import_seed_rows(seed)


@pytest.mark.smoke
def test_import_seed_file_idempotent(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    apply_network_paths(paths)
    ensure_categories_for_mvr_bind(paths)
    reset_entity_registry()
    first = import_seed_file(paths.seed_path)
    second = import_seed_file(paths.seed_path)
    assert first == 15
    assert second == 15
    payload = json.loads(paths.entities_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 15


@pytest.mark.smoke
def test_bootstrap_seed_at_paths_delegates(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    assert bootstrap_seed_at_paths(paths) == 15


@pytest.mark.smoke
def test_count_seed_rows(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    assert count_seed_rows(paths.seed_path) == 15
    assert count_seed_rows(tmp_path / "missing.json") == 0


@pytest.mark.smoke
def test_bootstrap_override_hook(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    specialists = paths.specialists_dir
    specialists.mkdir(parents=True, exist_ok=True)
    override = specialists / "bootstrap_specialist.py"
    override.write_text(
        """
from network.bootstrap.context import BootstrapContext, BootstrapResult

def run_bootstrap(ctx: BootstrapContext) -> BootstrapResult:
    return BootstrapResult(
        entities_committed=42,
        sources_processed=["override"],
        handler_id="test_override",
    )
""",
        encoding="utf-8",
    )
    result = run_network_bootstrap(paths)
    assert result.handler_id == "test_override"
    assert result.entities_committed == 42
    assert result.sources_processed == ["override"]
    registry = get_entity_registry()
    assert len(registry.list_entities()) == 0

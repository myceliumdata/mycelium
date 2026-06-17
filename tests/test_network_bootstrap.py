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
from network.example import copy_example_network
from network_helpers import copy_crm_network_manifest
from network.paths import NetworkPaths, apply_network_paths
from network.seed_import import bootstrap_seed_at_paths, count_seed_rows

REPO_ROOT = Path(__file__).resolve().parent.parent
CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm" / "seed.json"
CRM_MANIFEST = REPO_ROOT / "examples" / "networks" / "crm" / "network.json"
FRAMEWORK_BOOTSTRAP = {
    "module": "network.bootstrap.handlers.default_seed",
    "handler": "DefaultSeedHandler",
}


def _write_manifest(root: Path, bootstrap: dict | None, *, base: Path | None = None) -> None:
    src = base or CRM_MANIFEST
    manifest = json.loads(src.read_text(encoding="utf-8"))
    if bootstrap is None:
        manifest.pop("bootstrap", None)
    else:
        manifest["bootstrap"] = bootstrap
    (root / "network.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _prepare_root(tmp_path: Path, *, seed_src: Path | None = None) -> NetworkPaths:
    root = tmp_path / "net"
    root.mkdir(parents=True, exist_ok=True)
    if seed_src is not None:
        shutil.copy(seed_src, root / "seed.json")
    shutil.copy(CRM_MANIFEST, root / "network.json")
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
def test_run_network_bootstrap_missing_bootstrap_block(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    _write_manifest(paths.root, None)
    with pytest.raises(ValueError, match="missing required 'bootstrap'"):
        run_network_bootstrap(paths)


@pytest.mark.smoke
def test_run_network_bootstrap_missing_module(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    _write_manifest(paths.root, {"handler": "DefaultSeedHandler"})
    with pytest.raises(ValueError, match="bootstrap.module is required"):
        run_network_bootstrap(paths)


@pytest.mark.smoke
def test_run_network_bootstrap_missing_handler(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    _write_manifest(
        paths.root,
        {"module": "network.bootstrap.handlers.default_seed"},
    )
    with pytest.raises(ValueError, match="bootstrap.handler is required"):
        run_network_bootstrap(paths)


@pytest.mark.smoke
def test_run_network_bootstrap_rejects_legacy_handler_only(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    _write_manifest(paths.root, {"handler": "default_seed"})
    with pytest.raises(ValueError, match="bootstrap.module is required"):
        run_network_bootstrap(paths)


@pytest.mark.smoke
def test_framework_handler_does_not_require_network_root_module(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    assert not (paths.root / "bootstrap_handlers").exists()
    result = run_network_bootstrap(paths)
    assert result.entities_committed == 15
    assert result.handler_id == "default_seed"


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
    copy_crm_network_manifest(tmp_path)
    apply_network_paths(NetworkPaths.from_root(tmp_path))
    ensure_categories_for_mvr_bind(NetworkPaths.from_root(tmp_path))
    reset_entity_registry()
    with pytest.raises(ValueError, match="bind field 'employer'"):
        import_seed_rows(seed)


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
def test_pack_handler_from_network_root(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    handlers_dir = paths.root / "bootstrap_handlers"
    handlers_dir.mkdir(parents=True, exist_ok=True)
    (handlers_dir / "pack_handler.py").write_text(
        '''
from network.bootstrap.context import BootstrapContext, BootstrapResult

class PackHandler:
    def run(self, ctx: BootstrapContext) -> BootstrapResult:
        return BootstrapResult(
            entities_committed=42,
            sources_processed=["pack"],
            handler_id="pack_stub",
        )
''',
        encoding="utf-8",
    )
    _write_manifest(
        paths.root,
        {
            "module": "bootstrap_handlers.pack_handler",
            "handler": "PackHandler",
        },
    )
    result = run_network_bootstrap(paths)
    assert result.handler_id == "pack_stub"
    assert result.entities_committed == 42
    assert result.sources_processed == ["pack"]
    assert len(get_entity_registry().list_entities()) == 0


@pytest.mark.smoke
def test_pack_handler_import_failure(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    _write_manifest(
        paths.root,
        {
            "module": "bootstrap_handlers.missing_module",
            "handler": "MissingHandler",
        },
    )
    with pytest.raises(ValueError, match="Cannot import bootstrap pack module"):
        run_network_bootstrap(paths)


@pytest.mark.smoke
def test_pack_handler_receives_guide_text(tmp_path: Path) -> None:
    paths = _prepare_root(tmp_path, seed_src=CRM_SEED)
    shutil.copy(
        REPO_ROOT / "examples" / "networks" / "crm" / "guide.md",
        paths.root / "guide.md",
    )
    handlers_dir = paths.root / "bootstrap_handlers"
    handlers_dir.mkdir(parents=True, exist_ok=True)
    (handlers_dir / "guide_probe.py").write_text(
        '''
from network.bootstrap.context import BootstrapContext, BootstrapResult

class GuideProbeHandler:
    def run(self, ctx: BootstrapContext) -> BootstrapResult:
        assert ctx.guide_text is not None
        assert "investor" in ctx.guide_text.lower()
        return BootstrapResult(
            entities_committed=0,
            sources_processed=[],
            handler_id="guide_probe",
        )
''',
        encoding="utf-8",
    )
    _write_manifest(
        paths.root,
        {
            "module": "bootstrap_handlers.guide_probe",
            "handler": "GuideProbeHandler",
        },
    )
    result = run_network_bootstrap(paths)
    assert result.handler_id == "guide_probe"


@pytest.mark.smoke
def test_copy_example_network_includes_bootstrap_handlers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples = tmp_path / "examples" / "networks"
    example = examples / "pack-demo"
    example.mkdir(parents=True)
    (example / "network.json").write_text(
        json.dumps({"name": "pack-demo", "bootstrap": FRAMEWORK_BOOTSTRAP}),
        encoding="utf-8",
    )
    handlers = example / "bootstrap_handlers"
    handlers.mkdir()
    (handlers / "handler.py").write_text("class Stub: pass\n", encoding="utf-8")
    monkeypatch.setattr("network.example.examples_root", lambda: examples)
    target = tmp_path / "live"
    copied = copy_example_network("pack-demo", target)
    assert "bootstrap_handlers" in copied
    assert (target / "bootstrap_handlers" / "handler.py").is_file()

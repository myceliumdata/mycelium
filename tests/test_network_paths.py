"""Smoke tests for network_root resolution and path wiring."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from network.paths import (
    NetworkPaths,
    apply_network_paths,
    framework_root,
    network_display_name,
    resolve_network_root,
)


@pytest.mark.smoke
def test_network_paths_from_root(tmp_path: Path) -> None:
    root = tmp_path / "my_network"
    root.mkdir()
    (root / "seed.json").write_text(json.dumps({"people": []}), encoding="utf-8")

    paths = NetworkPaths.from_root(root)

    assert paths.root == root.resolve()
    assert paths.seed_path == root / "seed.json"
    assert paths.registry_path == root / "agent_registry.json"
    assert paths.categories_path == root / "categories.json"
    assert paths.agents_dir == root / "agents"
    assert paths.checkpoint_path == root / "checkpoints.sqlite"
    assert paths.db_path == root / "mycelium.db"


@pytest.mark.smoke
def test_resolve_legacy_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    framework = tmp_path / "framework"
    framework.mkdir()
    legacy_data = framework / "data"
    legacy_data.mkdir()

    monkeypatch.delenv("MYCELIUM_NETWORK_ROOT", raising=False)
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(framework))

    assert resolve_network_root() == legacy_data.resolve()


@pytest.mark.smoke
def test_resolve_env_network_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_net = tmp_path / "env_network"
    env_net.mkdir()
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(env_net))

    assert resolve_network_root() == env_net.resolve()


@pytest.mark.smoke
def test_cli_network_dir_overrides_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_net = tmp_path / "env_network"
    cli_net = tmp_path / "cli_network"
    env_net.mkdir()
    cli_net.mkdir()
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(env_net))

    assert resolve_network_root(cli_network_dir=str(cli_net)) == cli_net.resolve()


@pytest.mark.smoke
def test_apply_network_paths_sets_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "MYCELIUM_NETWORK_ROOT",
        "MYCELIUM_SEED_PATH",
        "MYCELIUM_AGENT_REGISTRY_PATH",
        "MYCELIUM_CATEGORIES_PATH",
        "MYCELIUM_AGENT_DATA_DIR",
        "MYCELIUM_CHECKPOINT_PATH",
        "MYCELIUM_DB_PATH",
    ):
        monkeypatch.delenv(key, raising=False)

    paths = NetworkPaths.from_root(tmp_path / "net")
    apply_network_paths(paths)

    assert Path(os.environ["MYCELIUM_NETWORK_ROOT"]) == paths.root
    assert Path(os.environ["MYCELIUM_SEED_PATH"]) == paths.seed_path
    assert Path(os.environ["MYCELIUM_AGENT_REGISTRY_PATH"]) == paths.registry_path
    assert Path(os.environ["MYCELIUM_CATEGORIES_PATH"]) == paths.categories_path
    assert Path(os.environ["MYCELIUM_AGENT_DATA_DIR"]) == paths.agents_dir
    assert Path(os.environ["MYCELIUM_CHECKPOINT_PATH"]) == paths.checkpoint_path
    assert Path(os.environ["MYCELIUM_DB_PATH"]) == paths.db_path


@pytest.mark.smoke
def test_network_display_name_from_json(tmp_path: Path) -> None:
    root = tmp_path / "named_net"
    root.mkdir()
    (root / "network.json").write_text(
        json.dumps({"display_name": "PRM CRM"}),
        encoding="utf-8",
    )
    paths = NetworkPaths.from_root(root)
    assert network_display_name(paths) == "PRM CRM"


@pytest.mark.smoke
def test_framework_root_from_package_location() -> None:
    root = framework_root()
    assert (root / "src" / "network" / "paths.py").is_file()

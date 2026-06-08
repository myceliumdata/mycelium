"""Smoke tests for network_root resolution and path wiring."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from network_helpers import clear_network_path_env
from network.paths import (
    NetworkPaths,
    apply_network_paths,
    framework_root,
    network_display_name,
    resolve_network_root,
    runtime_path,
    shell_export_network_paths,
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
    assert paths.specialists_dir == root / "specialists"
    assert paths.checkpoint_path == root / "checkpoints.sqlite"
    assert paths.db_path == root / "mycelium.db"


@pytest.mark.smoke
def test_resolve_raises_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("MYCELIUM_NETWORK_ROOT", raising=False)
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing-networks.json"))
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(tmp_path / "framework"))

    with pytest.raises(ValueError, match="refresh-example-network"):
        resolve_network_root()


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
    assert Path(os.environ["MYCELIUM_SPECIALISTS_DIR"]) == paths.specialists_dir
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
def test_runtime_path_fails_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_network_path_env(monkeypatch)
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing-networks.json"))
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(tmp_path / "framework"))

    with pytest.raises(ValueError, match="refresh-example-network"):
        runtime_path("MYCELIUM_CHECKPOINT_PATH")


@pytest.mark.smoke
def test_runtime_path_derives_from_network_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_network_path_env(monkeypatch)
    root = tmp_path / "net"
    root.mkdir()
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))

    assert runtime_path("MYCELIUM_CHECKPOINT_PATH") == root / "checkpoints.sqlite"
    assert runtime_path("MYCELIUM_AGENT_REGISTRY_PATH") == root / "agent_registry.json"
    assert runtime_path("MYCELIUM_SEED_PATH") == root / "seed.json"
    assert runtime_path("MYCELIUM_AGENT_DATA_DIR") == root / "agents"
    assert runtime_path("MYCELIUM_SPECIALISTS_DIR") == root / "specialists"


@pytest.mark.smoke
def test_runtime_path_respects_explicit_env_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "net"
    root.mkdir()
    custom = tmp_path / "custom_categories.json"
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(custom))

    assert runtime_path("MYCELIUM_CATEGORIES_PATH") == custom.resolve()


@pytest.mark.smoke
def test_shell_export_network_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "exported_net"
    root.mkdir()
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(root))

    exports = shell_export_network_paths()

    assert "export MYCELIUM_NETWORK_ROOT=" in exports
    assert "export MYCELIUM_CHECKPOINT_PATH=" in exports
    assert str(root / "checkpoints.sqlite") in exports


@pytest.mark.smoke
def test_framework_root_from_package_location() -> None:
    root = framework_root()
    assert (root / "src" / "network" / "paths.py").is_file()


@pytest.mark.smoke
def test_specialists_dir_isolated_per_network_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each network_root gets its own specialists/ tree via apply_network_paths."""
    import inspect

    from agents.factory.agent_factory import AgentFactory, reset_agent_factory
    from agents.registry import get_agent_registry, reset_agent_registry

    net_a = tmp_path / "net_a"
    net_b = tmp_path / "net_b"
    net_a.mkdir()
    net_b.mkdir()

    descriptions: dict[str, str] = {}

    for net, label in ((net_a, "NET_A"), (net_b, "NET_B")):
        clear_network_path_env(monkeypatch)
        apply_network_paths(NetworkPaths.from_root(net))
        reset_agent_registry()
        reset_agent_factory()

        description = f"Foo specialist for {label}"
        descriptions[label] = description
        factory = AgentFactory()
        info = factory.create_specialist(
            "foo",
            "foo_specialist",
            description,
            auto_commit=False,
        )
        assert info["created"] is True
        py_path = net / "specialists" / "foo_specialist.py"
        assert py_path.is_file()
        assert description in py_path.read_text(encoding="utf-8")

    assert (
        (net_a / "specialists" / "foo_specialist.py").read_text(encoding="utf-8")
        != (net_b / "specialists" / "foo_specialist.py").read_text(encoding="utf-8")
    )

    clear_network_path_env(monkeypatch)
    apply_network_paths(NetworkPaths.from_root(net_b))
    reset_agent_registry()
    reset_agent_factory()

    registry = get_agent_registry()
    fn = registry.get_agent_fn("foo_specialist")
    assert callable(fn)
    mod = inspect.getmodule(fn)
    assert mod is not None
    assert Path(mod.__file__).resolve() == (net_b / "specialists" / "foo_specialist.py").resolve()
    assert descriptions["NET_B"] in Path(mod.__file__).read_text(encoding="utf-8")

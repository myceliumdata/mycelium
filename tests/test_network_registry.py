"""Smoke tests for the user-local network name registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from network.paths import resolve_network_root
from network.registry import (
    list_networks,
    load_network_registry,
    network_root_status,
    networks_config_path,
    register_network,
    set_default_network,
    unregister_network,
)


@pytest.fixture
def networks_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    config = tmp_path / "networks.json"
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(config))
    monkeypatch.delenv("MYCELIUM_NETWORK_ROOT", raising=False)
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    return config


@pytest.mark.smoke
def test_networks_config_path_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    custom = tmp_path / "custom-networks.json"
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(custom))
    assert networks_config_path() == custom.resolve()


@pytest.mark.smoke
def test_register_list_and_persist(networks_config: Path, tmp_path: Path) -> None:
    root = tmp_path / "crm-seeded"
    root.mkdir()

    entry = register_network("prm_crm", root, default=True)
    assert entry.name == "prm_crm"
    assert Path(entry.root) == root.resolve()
    assert entry.default is True
    assert networks_config.is_file()

    entries = list_networks()
    assert len(entries) == 1
    assert entries[0].name == "prm_crm"
    assert load_network_registry()[0].default is True


@pytest.mark.smoke
def test_first_registration_becomes_default(networks_config: Path, tmp_path: Path) -> None:
    root = tmp_path / "only"
    root.mkdir()
    entry = register_network("solo", root)
    assert entry.default is True


@pytest.mark.smoke
def test_set_default_network(networks_config: Path, tmp_path: Path) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    register_network("net_a", root_a, default=True)
    register_network("net_b", root_b)

    entry = set_default_network("net_b")
    assert entry.default is True
    entries = {item.name: item.default for item in list_networks()}
    assert entries == {"net_a": False, "net_b": True}


@pytest.mark.smoke
def test_update_default_network_root_preserves_default(
    networks_config: Path, tmp_path: Path
) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    register_network("net_a", root_a, default=True)
    register_network("net_b", root_b)

    updated = register_network("net_a", root_b)
    assert updated.default is True
    assert Path(updated.root) == root_b.resolve()
    entries = {item.name: item.default for item in list_networks()}
    assert entries == {"net_a": True, "net_b": False}


@pytest.mark.smoke
def test_default_network_beats_legacy_shim(
    networks_config: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    framework = tmp_path / "framework"
    framework.mkdir()
    legacy_data = framework / "data"
    legacy_data.mkdir()
    registered = tmp_path / "registered"
    registered.mkdir()

    networks_config.write_text(
        json.dumps(
            {
                "version": "1",
                "networks": [
                    {
                        "name": "test_net",
                        "root": str(registered.resolve()),
                        "default": True,
                    },
                ],
            },
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(framework))

    assert resolve_network_root() == registered.resolve()


@pytest.mark.smoke
def test_cli_network_name_beats_env_root(
    networks_config: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    named = tmp_path / "named"
    env_only = tmp_path / "env_only"
    named.mkdir()
    env_only.mkdir()
    register_network("named_net", named, default=True)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(env_only))

    assert resolve_network_root(cli_network_name="named_net") == named.resolve()


@pytest.mark.smoke
def test_env_network_name_beats_default(
    networks_config: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    default_root = tmp_path / "default"
    env_named = tmp_path / "env_named"
    default_root.mkdir()
    env_named.mkdir()
    register_network("default_net", default_root, default=True)
    register_network("other_net", env_named)
    monkeypatch.setenv("MYCELIUM_NETWORK", "other_net")

    assert resolve_network_root() == env_named.resolve()


@pytest.mark.smoke
def test_unknown_network_name_raises(
    networks_config: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    framework = tmp_path / "framework"
    framework.mkdir()
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(framework))

    with pytest.raises(ValueError, match="Unknown network"):
        resolve_network_root(cli_network_name="missing")


@pytest.mark.smoke
def test_register_rejects_duplicate_on_save_validation(
    networks_config: Path, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    register_network("dup", root, default=True)
    other = tmp_path / "other"
    other.mkdir()
    register_network("other", other)

    networks_config.write_text(
        json.dumps(
            {
                "version": "1",
                "networks": [
                    {"name": "a", "root": str(root.resolve()), "default": True},
                    {"name": "a", "root": str(other.resolve()), "default": False},
                ],
            },
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate network name"):
        load_network_registry()


@pytest.mark.smoke
def test_network_root_status_missing_and_uninitialized(tmp_path: Path) -> None:
    missing = tmp_path / "gone"
    empty = tmp_path / "empty"
    empty.mkdir()
    initialized = tmp_path / "ready"
    initialized.mkdir()
    (initialized / "network.json").write_text("{}", encoding="utf-8")

    assert network_root_status(missing) == "missing"
    assert network_root_status(empty) == "uninitialized"
    assert network_root_status(initialized) == "ok"


@pytest.mark.smoke
def test_resolve_registered_network_missing_root_raises(
    networks_config: Path,
    tmp_path: Path,
) -> None:
    stale_root = tmp_path / "stale"
    networks_config.write_text(
        json.dumps(
            {
                "version": "1",
                "networks": [
                    {
                        "name": "stale_net",
                        "root": str(stale_root.resolve()),
                        "default": True,
                    },
                ],
            },
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing path"):
        resolve_network_root(cli_network_name="stale_net")


@pytest.mark.smoke
def test_unregister_network_removes_entry_and_reassigns_default(
    networks_config: Path,
    tmp_path: Path,
) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    (root_a / "network.json").write_text("{}", encoding="utf-8")
    (root_b / "network.json").write_text("{}", encoding="utf-8")
    register_network("net_a", root_a, default=True)
    register_network("net_b", root_b)

    removed = unregister_network("net_a")
    assert removed is not None
    assert removed.name == "net_a"
    entries = list_networks()
    assert len(entries) == 1
    assert entries[0].name == "net_b"
    assert entries[0].default is True


@pytest.mark.smoke
def test_unregister_unknown_network_returns_none(networks_config: Path) -> None:
    assert unregister_network("missing") is None

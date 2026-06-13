"""Shared helpers for network path isolation in tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

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
        if monkeypatch is not None:
            monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
            monkeypatch.setenv("MYCELIUM_SEED_PATH", str(dest))
            monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
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
    """Import ``root/seed.json`` when present (uses ``apply_network_paths``)."""
    from agents.entity_registry import reset_entity_registry
    from network.paths import NetworkPaths, apply_network_paths
    from network.seed_import import import_seed_file

    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)
    from network.category_mvr_bootstrap import ensure_categories_for_mvr_bind

    ensure_categories_for_mvr_bind(paths)
    reset_entity_registry()
    return import_seed_file(paths.seed_path)

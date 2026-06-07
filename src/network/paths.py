"""Resolve network_root and derive runtime paths for seed, storage, and agents."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


def framework_root() -> Path:
    """Return the Mycelium framework (repo) root directory.

    Precedence: ``MYCELIUM_FRAMEWORK_ROOT`` env, else infer from this package
    location (``src/network/paths.py`` → three parents up).
    """
    env = os.getenv("MYCELIUM_FRAMEWORK_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent.parent


def resolve_network_root(*, cli_network_dir: str | None = None) -> Path:
    """Resolve the active network data root.

    Precedence (Phase 2): CLI ``--network-dir`` → env ``MYCELIUM_NETWORK_ROOT``
    → legacy ``<framework>/data``.
    """
    if cli_network_dir:
        return Path(cli_network_dir).expanduser().resolve()
    env_root = os.getenv("MYCELIUM_NETWORK_ROOT", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()
    return (framework_root() / "data").resolve()


@dataclass(frozen=True)
class NetworkPaths:
    """Standard layout paths under a single network_root."""

    root: Path
    seed_path: Path
    registry_path: Path
    categories_path: Path
    agents_dir: Path
    checkpoint_path: Path
    db_path: Path

    @classmethod
    def from_root(cls, root: Path) -> NetworkPaths:
        resolved = root.expanduser().resolve()
        return cls(
            root=resolved,
            seed_path=resolved / "seed.json",
            registry_path=resolved / "agent_registry.json",
            categories_path=resolved / "categories.json",
            agents_dir=resolved / "agents",
            checkpoint_path=resolved / "checkpoints.sqlite",
            db_path=resolved / "mycelium.db",
        )


def apply_network_paths(paths: NetworkPaths) -> None:
    """Set MYCELIUM_* env vars consumed by seed, registry, storage, and graphs."""
    os.environ["MYCELIUM_NETWORK_ROOT"] = str(paths.root)
    os.environ["MYCELIUM_SEED_PATH"] = str(paths.seed_path)
    os.environ["MYCELIUM_AGENT_REGISTRY_PATH"] = str(paths.registry_path)
    os.environ["MYCELIUM_CATEGORIES_PATH"] = str(paths.categories_path)
    os.environ["MYCELIUM_AGENT_DATA_DIR"] = str(paths.agents_dir)
    os.environ["MYCELIUM_CHECKPOINT_PATH"] = str(paths.checkpoint_path)
    os.environ["MYCELIUM_DB_PATH"] = str(paths.db_path)


def network_display_name(paths: NetworkPaths) -> str | None:
    """Read optional display name from ``network_root/network.json``."""
    network_json = paths.root / "network.json"
    if not network_json.is_file():
        return None
    try:
        data = json.loads(network_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    for key in ("display_name", "name"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None

"""Resolve network_root and derive runtime paths for seed, storage, and agents."""

from __future__ import annotations

import json
import os
import shlex
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


def legacy_network_root() -> Path:
    """Return the retired prototype shim path ``<framework>/data`` (tests only)."""
    return (framework_root() / "data").resolve()


NO_NETWORK_CONFIGURED_MSG = (
    "No network configured. Run: ./bin/refresh-example-network crm"
)


def resolve_network_root(
    *,
    cli_network_dir: str | None = None,
    cli_network_name: str | None = None,
) -> Path:
    """Resolve the active network data root.

    Precedence: CLI ``--network-dir`` → CLI ``--network`` (registry name) → env
    ``MYCELIUM_NETWORK_ROOT`` → env ``MYCELIUM_NETWORK`` (name) → default from
    registry. Raises ``ValueError`` when nothing is configured.
    """
    from network.registry import default_network_root, resolve_root_by_name

    if cli_network_dir:
        return Path(cli_network_dir).expanduser().resolve()
    if cli_network_name:
        root = resolve_root_by_name(cli_network_name)
        if root is None:
            raise ValueError(f"Unknown network: {cli_network_name}")
        return root
    env_root = os.getenv("MYCELIUM_NETWORK_ROOT", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()
    env_name = os.getenv("MYCELIUM_NETWORK", "").strip()
    if env_name:
        root = resolve_root_by_name(env_name)
        if root is None:
            raise ValueError(f"Unknown network: {env_name}")
        return root
    default_root = default_network_root()
    if default_root is not None:
        return default_root
    raise ValueError(NO_NETWORK_CONFIGURED_MSG)


@dataclass(frozen=True)
class NetworkPaths:
    """Standard layout paths under a single network_root.

    ``specialists/`` holds generated ``*_specialist.py`` modules (per-network).
    """

    root: Path
    seed_path: Path
    registry_path: Path
    categories_path: Path
    agents_dir: Path
    specialists_dir: Path
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
            specialists_dir=resolved / "specialists",
            checkpoint_path=resolved / "checkpoints.sqlite",
            db_path=resolved / "mycelium.db",
        )


_RUNTIME_ENV_FIELDS: dict[str, str] = {
    "MYCELIUM_SEED_PATH": "seed_path",
    "MYCELIUM_AGENT_REGISTRY_PATH": "registry_path",
    "MYCELIUM_CATEGORIES_PATH": "categories_path",
    "MYCELIUM_AGENT_DATA_DIR": "agents_dir",
    "MYCELIUM_SPECIALISTS_DIR": "specialists_dir",
    "MYCELIUM_CHECKPOINT_PATH": "checkpoint_path",
    "MYCELIUM_DB_PATH": "db_path",
}


def _paths_for_runtime() -> NetworkPaths:
    """Derive ``NetworkPaths`` from ``MYCELIUM_NETWORK_ROOT`` or registry resolution."""
    env_root = os.getenv("MYCELIUM_NETWORK_ROOT", "").strip()
    if env_root:
        return NetworkPaths.from_root(Path(env_root))
    return NetworkPaths.from_root(resolve_network_root())


def runtime_path(env_var: str) -> Path:
    """Resolve a runtime artifact path (never repo-root ``data/``).

    Precedence: explicit ``env_var`` → ``MYCELIUM_NETWORK_ROOT`` derivation →
    ``resolve_network_root()`` derivation. Raises ``ValueError`` when unconfigured.
    """
    field = _RUNTIME_ENV_FIELDS.get(env_var)
    if field is None:
        raise ValueError(f"Unknown runtime path env var: {env_var}")
    explicit = os.getenv(env_var, "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    paths = _paths_for_runtime()
    return getattr(paths, field)


def shell_export_network_paths() -> str:
    """Return bash ``export`` lines for all ``MYCELIUM_*`` path vars (Studio bootstrap)."""
    paths = NetworkPaths.from_root(resolve_network_root())
    lines = [f"export MYCELIUM_NETWORK_ROOT={shlex.quote(str(paths.root))}"]
    for env_var, field in _RUNTIME_ENV_FIELDS.items():
        value = getattr(paths, field)
        lines.append(f"export {env_var}={shlex.quote(str(value))}")
    return "\n".join(lines)


def apply_network_paths(paths: NetworkPaths) -> None:
    """Set MYCELIUM_* env vars consumed by seed, registry, storage, and graphs."""
    os.environ["MYCELIUM_NETWORK_ROOT"] = str(paths.root)
    for env_var, field in _RUNTIME_ENV_FIELDS.items():
        os.environ[env_var] = str(getattr(paths, field))


def network_metadata(*, root: Path | None = None) -> dict[str, str | None]:
    """Resolved network_root plus optional name metadata from registry / network.json."""
    from network.registry import load_network_registry

    resolved_root = (root or resolve_network_root()).expanduser().resolve()
    paths = NetworkPaths.from_root(resolved_root)
    display_name = network_display_name(paths)

    network_name: str | None = os.getenv("MYCELIUM_NETWORK", "").strip() or None
    if not network_name:
        for entry in load_network_registry():
            if Path(entry.root).expanduser().resolve() == resolved_root:
                network_name = entry.name
                break
    if not network_name:
        network_json = resolved_root / "network.json"
        if network_json.is_file():
            try:
                data = json.loads(network_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = None
            if isinstance(data, dict):
                raw = data.get("name")
                if isinstance(raw, str) and raw.strip():
                    network_name = raw.strip()

    return {
        "network_root": str(resolved_root),
        "network_name": network_name,
        "network_display_name": display_name,
    }


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

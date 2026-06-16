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
    entities_path: Path
    registry_path: Path
    categories_path: Path
    agents_dir: Path
    specialists_dir: Path
    checkpoint_path: Path
    db_path: Path
    entitlements_path: Path
    quotes_path: Path
    deliveries_path: Path
    credits_path: Path

    @classmethod
    def from_root(cls, root: Path) -> NetworkPaths:
        resolved = root.expanduser().resolve()
        return cls(
            root=resolved,
            seed_path=resolved / "seed.json",
            entities_path=_default_entity_store_path(resolved),
            registry_path=resolved / "agent_registry.json",
            categories_path=resolved / "categories.json",
            agents_dir=resolved / "agents",
            specialists_dir=resolved / "specialists",
            checkpoint_path=resolved / "checkpoints.sqlite",
            db_path=resolved / "mycelium.db",
            entitlements_path=resolved / "entitlements.json",
            quotes_path=resolved / "quotes.json",
            deliveries_path=resolved / "deliveries.json",
            credits_path=resolved / "credits.json",
        )


def _provisional_paths(root: Path) -> NetworkPaths:
    """Build ``NetworkPaths`` before entity store resolution (internal)."""
    return NetworkPaths(
        root=root,
        seed_path=root / "seed.json",
        entities_path=root / "entities.json",
        registry_path=root / "agent_registry.json",
        categories_path=root / "categories.json",
        agents_dir=root / "agents",
        specialists_dir=root / "specialists",
        checkpoint_path=root / "checkpoints.sqlite",
        db_path=root / "mycelium.db",
        entitlements_path=root / "entitlements.json",
        quotes_path=root / "quotes.json",
        deliveries_path=root / "deliveries.json",
        credits_path=root / "credits.json",
    )


def _default_entity_store_path(root: Path) -> Path:
    """Default-grain entity store path from ``network.json`` (or CRM default)."""
    provisional = _provisional_paths(root)
    try:
        from network.mvr import default_mvr_grain

        grain = default_mvr_grain(paths=provisional)
        return entity_store_path(provisional, grain)
    except Exception:
        return root / "entities" / "person.json"


def entity_store_path(paths: NetworkPaths, grain: str) -> Path:
    """Canonical write path for a grain's entity store."""
    from network.mvr import load_mvr_config

    config = load_mvr_config(paths=paths)
    if grain not in config.grains:
        known = ", ".join(sorted(config.grains.keys()))
        raise ValueError(
            f"Unknown MVR grain {grain!r}; declared grains: {known}",
        )
    return paths.root / config.grains[grain].entities_file


def resolve_entity_store_path(paths: NetworkPaths, grain: str) -> Path:
    """Grain entity path with legacy root ``entities.json`` read fallback."""
    grain_path = entity_store_path(paths, grain)
    if grain_path.is_file():
        return grain_path
    legacy = paths.root / "entities.json"
    if legacy.is_file():
        return legacy
    return grain_path


_RUNTIME_ENV_FIELDS: dict[str, str] = {
    "MYCELIUM_SEED_PATH": "seed_path",
    "MYCELIUM_ENTITIES_PATH": "entities_path",
    "MYCELIUM_AGENT_REGISTRY_PATH": "registry_path",
    "MYCELIUM_CATEGORIES_PATH": "categories_path",
    "MYCELIUM_AGENT_DATA_DIR": "agents_dir",
    "MYCELIUM_SPECIALISTS_DIR": "specialists_dir",
    "MYCELIUM_CHECKPOINT_PATH": "checkpoint_path",
    "MYCELIUM_DB_PATH": "db_path",
    "MYCELIUM_ENTITLEMENTS_PATH": "entitlements_path",
    "MYCELIUM_QUOTES_PATH": "quotes_path",
    "MYCELIUM_DELIVERIES_PATH": "deliveries_path",
    "MYCELIUM_CREDITS_PATH": "credits_path",
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

    network_name: str | None = None
    if root is None:
        network_name = os.getenv("MYCELIUM_NETWORK", "").strip() or None
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

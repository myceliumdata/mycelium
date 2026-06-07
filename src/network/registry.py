"""User-local registry mapping network names to network_root paths."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field


class NetworkEntry(BaseModel):
    """A registered network name → root path mapping."""

    name: str
    root: str
    default: bool = False


class NetworksRegistryData(BaseModel):
    """Serializable networks config (``networks.json``)."""

    version: str = "1"
    networks: list[NetworkEntry] = Field(default_factory=list)


def networks_config_path() -> Path:
    """Return path to the networks config file."""
    env = os.getenv("MYCELIUM_NETWORKS_CONFIG", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".config" / "mycelium" / "networks.json").resolve()


def _normalize_root(root: str | Path) -> Path:
    path = Path(root).expanduser().resolve()
    if not path.is_absolute():
        raise ValueError(f"Network root must be an absolute path: {root}")
    return path


def _validate_registry(data: NetworksRegistryData) -> None:
    names: set[str] = set()
    defaults = 0
    for entry in data.networks:
        name = entry.name.strip()
        if not name:
            raise ValueError("Network name must not be empty")
        if name in names:
            raise ValueError(f"Duplicate network name: {name}")
        names.add(name)
        _normalize_root(entry.root)
        if entry.default:
            defaults += 1
    if data.networks and defaults != 1:
        raise ValueError(
            "Exactly one network must be marked default when any are registered",
        )


def _load_registry_data() -> NetworksRegistryData:
    path = networks_config_path()
    if not path.is_file():
        return NetworksRegistryData()
    raw = json.loads(path.read_text(encoding="utf-8"))
    data = NetworksRegistryData.model_validate(raw)
    _validate_registry(data)
    return data


def _save_registry_data(data: NetworksRegistryData) -> None:
    _validate_registry(data)
    path = networks_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = data.model_dump_json(indent=2) + "\n"
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_network_registry() -> list[NetworkEntry]:
    """Load registered networks from the user config file."""
    return list(_load_registry_data().networks)


def list_networks() -> list[NetworkEntry]:
    """Return all registered network entries."""
    return load_network_registry()


def resolve_root_by_name(name: str) -> Path | None:
    """Look up a registered network root by name."""
    target = name.strip()
    if not target:
        return None
    for entry in load_network_registry():
        if entry.name == target:
            return _normalize_root(entry.root)
    return None


def default_network_root() -> Path | None:
    """Return the root path of the default registered network, if any."""
    for entry in load_network_registry():
        if entry.default:
            return _normalize_root(entry.root)
    return None


def register_network(name: str, root: str | Path, *, default: bool = False) -> NetworkEntry:
    """Add or update a network entry in the user config."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Network name must not be empty")
    resolved_root = _normalize_root(root)
    data = _load_registry_data()
    existing = next(
        (entry for entry in data.networks if entry.name == clean_name),
        None,
    )
    networks = [entry for entry in data.networks if entry.name != clean_name]
    make_default = default or not networks or (existing.default if existing else False)
    if make_default:
        networks = [
            NetworkEntry(name=entry.name, root=entry.root, default=False)
            for entry in networks
        ]
    entry = NetworkEntry(
        name=clean_name,
        root=str(resolved_root),
        default=make_default,
    )
    networks.append(entry)
    _save_registry_data(NetworksRegistryData(version=data.version, networks=networks))
    return entry


def set_default_network(name: str) -> NetworkEntry:
    """Mark one registered network as the default."""
    clean_name = name.strip()
    data = _load_registry_data()
    if not any(entry.name == clean_name for entry in data.networks):
        raise ValueError(f"Unknown network: {clean_name}")
    updated: list[NetworkEntry] = []
    selected: NetworkEntry | None = None
    for entry in data.networks:
        is_default = entry.name == clean_name
        new_entry = NetworkEntry(
            name=entry.name,
            root=entry.root,
            default=is_default,
        )
        updated.append(new_entry)
        if is_default:
            selected = new_entry
    assert selected is not None
    _save_registry_data(NetworksRegistryData(version=data.version, networks=updated))
    return selected

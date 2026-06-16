"""Copy and refresh committed example networks into live network_root paths."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from network.paths import NetworkPaths, framework_root
from network.registry import load_network_registry, register_network
from network.seed_import import bootstrap_seed_at_paths, count_seed_rows

_SKIP_NAMES = frozenset(
    {
        "README.md",
        "prepare_seed.py",
        "categories.json",
        "entities.json",
        "entities",
        "deliveries.json",
        "agent_registry.json",
        "agents",
        "specialists",  # generated runtime modules — not copied from examples
        "checkpoints.sqlite",
        "mycelium.db",
    },
)
# ``bootstrap_handlers/`` is intentionally not skipped — network-pack handlers copy with refresh.
_RUNTIME_SUFFIXES = (".db", ".sqlite")


def examples_root() -> Path:
    """Return ``examples/networks`` under the framework root."""
    return framework_root() / "examples" / "networks"


def example_network_dir(name: str) -> Path:
    """Resolve and validate a committed example network directory."""
    source = examples_root() / name
    if not source.is_dir():
        raise ValueError(f"Unknown example network: {name}")
    return source


def _should_skip(item: Path) -> bool:
    if item.name in _SKIP_NAMES or item.name.startswith("."):
        return True
    if item.name.endswith((".sqlite-shm", ".sqlite-wal")):
        return True
    return item.is_file() and item.suffix in _RUNTIME_SUFFIXES


def copy_example_network(name: str, target: Path) -> list[str]:
    """Copy committed example files into ``target``; return copied entry names."""
    source = example_network_dir(name)
    target.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for item in sorted(source.iterdir()):
        if _should_skip(item):
            continue
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
        copied.append(item.name)
    return copied


def default_live_root(name: str) -> Path:
    """Default live network_root for an example name."""
    return (Path.home() / "mycelium-networks" / name).expanduser().resolve()


def resolve_registry_name(example: str, target: Path) -> str:
    """Registry name from ``network.json`` or the example folder name."""
    network_json = target / "network.json"
    if network_json.is_file():
        try:
            meta = json.loads(network_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = None
        if isinstance(meta, dict):
            raw = meta.get("name")
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
    return example


def live_root_exists(root: Path) -> bool:
    """True when the directory exists or any registry entry points at ``root``."""
    if root.is_dir():
        return True
    resolved = root.expanduser().resolve()
    for entry in load_network_registry():
        if Path(entry.root).expanduser().resolve() == resolved:
            return True
    return False


@dataclass(frozen=True)
class RefreshExampleResult:
    """Outcome of ``refresh_example_network``."""

    name: str
    root: Path
    source: Path
    copied: list[str]
    wiped: bool
    registered: bool
    registry_name: str | None
    is_default: bool
    seed_bootstrap_count: int = 0
    declined: bool = False
    dry_run: bool = False


def refresh_example_network(
    name: str,
    *,
    root: Path | None = None,
    register: bool = True,
    default: bool | None = None,
    no_default: bool = False,
    yes: bool = False,
    dry_run: bool = False,
    input_fn: Callable[[str], str] | None = None,
) -> RefreshExampleResult:
    """Bootstrap or reset a live network from ``examples/networks/<name>/``."""
    source = example_network_dir(name)
    live_root = (root or default_live_root(name)).expanduser().resolve()
    if not live_root.is_absolute():
        raise ValueError(f"Network root must be an absolute path: {live_root}")

    make_default = (name == "crm" and not no_default) if default is None else default
    exists = live_root_exists(live_root)
    wiped = False
    copied: list[str] = []
    registered = False
    registry_name: str | None = None

    if dry_run:
        would_copy = [
            item.name
            for item in sorted(source.iterdir())
            if not _should_skip(item)
        ]
        reg_name = resolve_registry_name(name, source) if register else None
        seed_bootstrap_count = (
            count_seed_rows(source / "seed.json")
            if "seed.json" in would_copy
            else 0
        )
        return RefreshExampleResult(
            name=name,
            root=live_root,
            source=source,
            copied=would_copy,
            wiped=exists,
            registered=register,
            registry_name=reg_name,
            is_default=make_default if register else False,
            seed_bootstrap_count=seed_bootstrap_count,
            dry_run=True,
        )

    if exists and not yes:
        prompt = input_fn or input
        answer = prompt(f"Replace network at {live_root}? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            return RefreshExampleResult(
                name=name,
                root=live_root,
                source=source,
                copied=[],
                wiped=False,
                registered=False,
                registry_name=None,
                is_default=False,
                declined=True,
                dry_run=False,
            )

    if exists:
        if live_root.is_dir():
            shutil.rmtree(live_root)
        wiped = True
    live_root.mkdir(parents=True, exist_ok=True)
    copied = copy_example_network(name, live_root)

    seed_bootstrap_count = 0
    if (live_root / "seed.json").is_file():
        seed_bootstrap_count = bootstrap_seed_at_paths(
            NetworkPaths.from_root(live_root),
        )

    if register:
        registry_name = resolve_registry_name(name, live_root)
        allow_no_default = no_default
        entry = register_network(
            registry_name,
            live_root,
            default=make_default,
            allow_no_default=allow_no_default,
        )
        registered = True
        make_default = entry.default

    return RefreshExampleResult(
        name=name,
        root=live_root,
        source=source,
        copied=copied,
        wiped=wiped,
        registered=registered,
        registry_name=registry_name,
        is_default=make_default if register else False,
        seed_bootstrap_count=seed_bootstrap_count,
    )

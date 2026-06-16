"""Stable imports for seed bootstrap (delegates to ``network.bootstrap``)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from network.bootstrap import run_network_bootstrap
from network.bootstrap.handlers.default_seed import import_seed_rows, load_seed_people
from network.paths import NetworkPaths

if TYPE_CHECKING:
    from agents.entity_registry import EntityRegistry
    from network.bootstrap.progress import BootstrapProgress


def _load_seed_people(seed_path: Path) -> list[dict]:
    """Backward-compatible alias for tests and internal callers."""
    return load_seed_people(seed_path)


def import_seed_file(
    seed_path: Path,
    *,
    registry: EntityRegistry | None = None,
) -> int:
    """Import seed people into ``entities.json`` via ``ensure_bound_entity``.

    Returns the number of rows processed, or ``0`` when ``seed_path`` is missing.
    Idempotent via registry ``bind_index``.
    """
    return import_seed_rows(seed_path, registry=registry)


def count_seed_rows(seed_path: Path) -> int:
    """Return the number of people rows in a seed file, or ``0`` when missing."""
    if not seed_path.is_file():
        return 0
    return len(load_seed_people(seed_path))


def bootstrap_seed_at_paths(
    paths: NetworkPaths,
    *,
    progress: BootstrapProgress | None = None,
) -> int:
    """Apply network paths, reset registry, run formal bootstrap when seed present."""
    return run_network_bootstrap(paths, progress=progress).entities_committed

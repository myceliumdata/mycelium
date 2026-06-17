"""Stable imports for seed bootstrap (delegates to ``network.bootstrap``)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from network.bootstrap import run_network_bootstrap
from network.bootstrap.handlers.default_seed import import_seed_rows, load_seed_rows
from network.paths import NetworkPaths

__all__ = [
    "bootstrap_seed_at_paths",
    "count_seed_rows",
    "import_seed_file",
    "import_seed_rows",
    "load_seed_rows",
]

if TYPE_CHECKING:
    from agents.entity_registry import EntityRegistry
    from network.bootstrap.progress import BootstrapProgress


def import_seed_file(
    seed_path: Path,
    *,
    registry: EntityRegistry | None = None,
    paths: NetworkPaths | None = None,
) -> int:
    """Import seed rows into entity store via ``ensure_entity_bind_fields``.

    Returns the number of rows processed, or ``0`` when ``seed_path`` is missing.
    Idempotent via registry ``bind_index``.
    """
    return import_seed_rows(seed_path, registry=registry, paths=paths)


def count_seed_rows(seed_path: Path) -> int:
    """Return the number of rows in a seed file, or ``0`` when missing."""
    if not seed_path.is_file():
        return 0
    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return 0
    return len(rows)


def bootstrap_seed_at_paths(
    paths: NetworkPaths,
    *,
    progress: BootstrapProgress | None = None,
) -> int:
    """Apply network paths, reset registry, run formal bootstrap when seed present."""
    return run_network_bootstrap(paths, progress=progress).entities_committed

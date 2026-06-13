"""Bootstrap import of ``seed.json`` rows into ``entities.json``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agents.entity_registry import reset_entity_registry
from network.category_mvr_bootstrap import ensure_categories_for_mvr_bind
from network.paths import NetworkPaths, apply_network_paths

if TYPE_CHECKING:
    from agents.entity_registry import EntityRegistry


def _load_seed_people(seed_path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid seed JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Seed JSON must be an object with a 'people' array")
    people = payload.get("people")
    if not isinstance(people, list):
        raise ValueError("Seed JSON must contain a 'people' array")
    for index, row in enumerate(people):
        if not isinstance(row, dict):
            raise ValueError(f"Seed people[{index}] must be an object")
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Seed people[{index}] must include a non-empty 'name'")
        employer = row.get("employer")
        if employer is not None and not isinstance(employer, str):
            raise ValueError(f"Seed people[{index}] 'employer' must be a string when present")
    return people


def import_seed_file(
    seed_path: Path,
    *,
    registry: EntityRegistry | None = None,
) -> int:
    """Import seed people into ``entities.json`` via ``ensure_bound_entity``.

    Returns the number of rows processed, or ``0`` when ``seed_path`` is missing.
    Idempotent via registry ``bind_index``.
    """
    if not seed_path.is_file():
        return 0

    people = _load_seed_people(seed_path)
    if registry is None:
        from agents.entity_registry import get_entity_registry

        registry = get_entity_registry()

    for row in people:
        name = str(row.get("name") or "").strip()
        employer = str(row.get("employer") or "").strip()
        registry.ensure_bound_entity(
            name,
            employer,
            source="seed_bootstrap",
            validation_state="validated",
        )
    return len(people)


def count_seed_rows(seed_path: Path) -> int:
    """Return the number of people rows in a seed file, or ``0`` when missing."""
    if not seed_path.is_file():
        return 0
    return len(_load_seed_people(seed_path))


def bootstrap_seed_at_paths(paths: NetworkPaths) -> int:
    """Apply network paths, reset registry, import ``seed.json`` when present."""
    apply_network_paths(paths)
    ensure_categories_for_mvr_bind(paths)
    reset_entity_registry()
    return import_seed_file(paths.seed_path)

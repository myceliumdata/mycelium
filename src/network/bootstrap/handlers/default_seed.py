"""Default CRM ``seed.json`` bootstrap handler."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from network.bootstrap.context import BootstrapContext, BootstrapResult

if TYPE_CHECKING:
    from agents.entity_registry import EntityRegistry


def load_seed_people(seed_path: Path) -> list[dict[str, Any]]:
    """Parse and validate ``seed.json`` ``people[]`` rows."""
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


def resolve_seed_grain() -> str:
    """Choose the grain that receives CRM-shaped seed rows."""
    from network.mvr import default_mvr_grain, load_mvr_config

    config = load_mvr_config()
    if "person" in config.grains:
        return "person"
    return default_mvr_grain()


def import_seed_rows(
    seed_path: Path,
    *,
    registry: EntityRegistry | None = None,
    grain: str | None = None,
) -> int:
    """Import seed people into the target grain entity store.

    Returns the number of rows processed, or ``0`` when ``seed_path`` is missing.
    Idempotent via registry ``bind_index``.
    """
    if not seed_path.is_file():
        return 0

    people = load_seed_people(seed_path)
    target_grain = grain or resolve_seed_grain()
    if registry is None:
        from agents.entity_registry import get_entity_registry

        registry = get_entity_registry(grain=target_grain)

    for row in people:
        name = str(row.get("name") or "").strip()
        employer = str(row.get("employer") or "").strip()
        if not employer:
            raise ValueError(
                "Seed people rows must include all MVR bind fields "
                f"(missing employer for {name!r})",
            )
        registry.ensure_bound_entity(
            name,
            employer,
            source="seed_bootstrap",
            validation_state="validated",
        )
    return len(people)


class DefaultSeedHandler:
    """Bootstrap handler for ``<network_root>/seed.json``."""

    def run(self, ctx: BootstrapContext) -> BootstrapResult:
        seed_path = ctx.paths.seed_path
        if not seed_path.is_file():
            return BootstrapResult(
                entities_committed=0,
                sources_processed=[],
                handler_id="default_seed",
            )
        grain = resolve_seed_grain()
        count = import_seed_rows(seed_path, grain=grain)
        return BootstrapResult(
            entities_committed=count,
            sources_processed=[str(seed_path.name)],
            handler_id="default_seed",
            entities_by_grain={grain: count},
        )

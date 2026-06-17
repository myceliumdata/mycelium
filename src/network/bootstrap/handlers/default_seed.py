"""Default JSON seed bootstrap handler."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agents.attribute_write import ensure_entity_bind_fields
from network.bootstrap.context import BootstrapContext, BootstrapResult

if TYPE_CHECKING:
    from agents.entity_registry import EntityRegistry
    from network.bootstrap.progress import BootstrapProgress


def load_seed_people(
    seed_path: Path,
    *,
    bind_fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Parse and validate ``seed.json`` ``people[]`` rows for active grain MVR."""
    if bind_fields is None:
        from network.mvr import load_mvr

        bind_fields = list(load_mvr(grain=resolve_seed_grain()).bind_fields)
    required = [field.strip().lower() for field in bind_fields if field.strip()]
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
        for field in required:
            raw = row.get(field)
            if raw is None or not str(raw).strip():
                raise ValueError(
                    f"Seed people[{index}] must include non-empty bind field {field!r}",
                )
    return people


def resolve_seed_grain() -> str:
    """Choose the grain that receives default seed rows."""
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
    progress: BootstrapProgress | None = None,
) -> int:
    """Import seed people into the target grain entity store.

    Returns the number of rows processed, or ``0`` when ``seed_path`` is missing.
    Idempotent via registry ``bind_index``.
    """
    if not seed_path.is_file():
        return 0

    target_grain = grain or resolve_seed_grain()
    if registry is None:
        from agents.entity_registry import get_entity_registry

        registry = get_entity_registry(grain=target_grain)

    mvr = registry._mvr
    bind_fields = [f.strip().lower() for f in mvr.bind_fields if f.strip()]
    people = load_seed_people(seed_path, bind_fields=list(mvr.bind_fields))
    total = len(people)
    for index, row in enumerate(people, start=1):
        bind_values = {
            field: str(row[field]).strip()
            for field in bind_fields
            if field in row
        }
        ensure_entity_bind_fields(
            bind_values,
            source="seed_bootstrap",
            validation_state="validated",
            registry=registry,
        )
        if progress is not None:
            progress.processing(index, total)
    return total


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
        count = import_seed_rows(seed_path, grain=grain, progress=ctx.progress)
        return BootstrapResult(
            entities_committed=count,
            sources_processed=[str(seed_path.name)],
            handler_id="default_seed",
            entities_by_grain={grain: count},
        )

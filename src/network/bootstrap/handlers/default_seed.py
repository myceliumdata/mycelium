"""Default JSON seed bootstrap handler."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agents.attribute_write import ensure_entity_bind_fields
from network.bootstrap.config import resolve_bootstrap_grain
from network.bootstrap.context import BootstrapContext, BootstrapResult

if TYPE_CHECKING:
    from agents.entity_registry import EntityRegistry
    from network.bootstrap.progress import BootstrapProgress
    from network.paths import NetworkPaths


def load_seed_rows(
    seed_path: Path,
    *,
    bind_fields: list[str] | None = None,
    paths: NetworkPaths | None = None,
    grain: str | None = None,
) -> list[dict[str, Any]]:
    """Parse and validate ``seed.json`` ``rows[]`` for the bootstrap grain MVR."""
    if bind_fields is None:
        from network.mvr import load_mvr

        if grain is None:
            if paths is None:
                raise ValueError("load_seed_rows requires paths or grain when bind_fields omitted")
            grain = resolve_bootstrap_grain(paths)
        bind_fields = list(load_mvr(grain=grain, paths=paths).bind_fields)
    required = [field.strip().lower() for field in bind_fields if field.strip()]
    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid seed JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Seed JSON must be an object with a 'rows' array")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Seed JSON must contain a 'rows' array")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Seed rows[{index}] must be an object")
        for field in required:
            raw = row.get(field)
            if raw is None or not str(raw).strip():
                raise ValueError(
                    f"Seed rows[{index}] must include non-empty bind field {field!r}",
                )
    return rows


def import_seed_rows(
    seed_path: Path,
    *,
    registry: EntityRegistry | None = None,
    grain: str | None = None,
    paths: NetworkPaths | None = None,
    progress: BootstrapProgress | None = None,
) -> int:
    """Import seed rows into the bootstrap grain entity store.

    Returns the number of rows processed, or ``0`` when ``seed_path`` is missing.
    Idempotent via registry ``bind_index``.
    """
    if not seed_path.is_file():
        return 0

    if grain is None:
        if paths is None:
            from network.paths import NetworkPaths

            env_root = os.getenv("MYCELIUM_NETWORK_ROOT", "").strip()
            if env_root:
                paths = NetworkPaths.from_root(Path(env_root))
            elif (seed_path.parent / "network.json").is_file():
                paths = NetworkPaths.from_root(seed_path.parent)
            else:
                raise ValueError("import_seed_rows requires paths or grain")
        grain = resolve_bootstrap_grain(paths)

    if registry is None:
        from agents.entity_registry import get_entity_registry

        registry = get_entity_registry(grain=grain)

    mvr = registry._mvr
    bind_fields = [field.strip().lower() for field in mvr.bind_fields if field.strip()]
    rows = load_seed_rows(
        seed_path,
        bind_fields=list(mvr.bind_fields),
        grain=grain,
        paths=paths,
    )
    total = len(rows)
    for index, row in enumerate(rows, start=1):
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
    """Bootstrap handler for ``<network_root>/seed.json`` (``rows[]`` → MVR bind fields)."""

    def run(self, ctx: BootstrapContext) -> BootstrapResult:
        seed_path = ctx.paths.seed_path
        if not seed_path.is_file():
            return BootstrapResult(
                entities_committed=0,
                sources_processed=[],
                handler_id="default_seed",
            )
        grain = resolve_bootstrap_grain(ctx.paths)
        count = import_seed_rows(
            seed_path,
            grain=grain,
            paths=ctx.paths,
            progress=ctx.progress,
        )
        return BootstrapResult(
            entities_committed=count,
            sources_processed=[str(seed_path.name)],
            handler_id="default_seed",
            entities_by_grain={grain: count},
        )

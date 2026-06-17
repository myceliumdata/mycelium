"""Runtime entity registry (per-grain entity stores) for provisional binds."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Iterator

from pydantic import BaseModel, Field

from agents.field_index import normalize_field_index_value
from storage.entity_store import EntityStore

if TYPE_CHECKING:
    from network.mvr import MvrPolicy

_registry: dict[str, EntityRegistry] = {}
_bootstrap_deferred_depth: int = 0


def _paths_for_runtime():
    from network.paths import _paths_for_runtime as _load_paths

    return _load_paths()


def _store_paths(json_path: Path) -> tuple[Path, Path]:
    stem = json_path.stem
    parent = json_path.parent
    return parent / f"{stem}.storage_strategy.json", parent / f"{stem}.sqlite"


@contextmanager
def bootstrap_deferred_save(
    *,
    before_commit: Callable[[], None] | None = None,
) -> Iterator[None]:
    """Defer entity store flushes for all grains during network bootstrap."""
    global _bootstrap_deferred_depth
    _bootstrap_deferred_depth += 1
    try:
        yield
    finally:
        _bootstrap_deferred_depth -= 1
        if _bootstrap_deferred_depth == 0:
            if before_commit is not None:
                before_commit()
            for registry in _registry.values():
                registry.commit_deferred_save()


def _resolve_registry_paths(grain: str) -> tuple[Path, str]:
    from network.mvr import default_mvr_grain
    from network.paths import entity_store_path

    resolved_grain = grain or default_mvr_grain()
    explicit = os.getenv("MYCELIUM_ENTITIES_PATH", "").strip()
    if explicit and resolved_grain == default_mvr_grain():
        path = Path(explicit).expanduser().resolve()
        return path, resolved_grain
    paths = _paths_for_runtime()
    return entity_store_path(paths, resolved_grain), resolved_grain


def require_full_bind_values(
    bind_values: dict[str, str],
    bind_fields: list[str],
) -> dict[str, str]:
    """Require every MVR bind field present and non-empty (no silent padding)."""
    fields = [field.strip().lower() for field in bind_fields if field.strip()]
    if not fields:
        raise ValueError("bind_fields must not be empty")
    normalized: dict[str, str] = {}
    missing: list[str] = []
    for field in fields:
        raw = bind_values.get(field)
        if raw is None or not str(raw).strip():
            missing.append(field)
        else:
            normalized[field] = str(raw).strip()
    if missing:
        raise ValueError(
            f"bind_values missing or empty MVR fields: {missing}",
        )
    return normalized


def make_bind_key(
    bind_values: dict[str, str],
    bind_fields: list[str],
) -> str:
    """Normalized compound bind index key from MVR bind field values."""
    fields = [field.strip().lower() for field in bind_fields if field.strip()]
    values = require_full_bind_values(bind_values, bind_fields)
    parts = [normalize_field_index_value(values[field]) for field in fields]
    return "|".join(parts)


class LegacyEntitiesSchemaError(ValueError):
    """entities.json row uses pre-Program-3 top-level name/employer without bind_values."""


def _reject_legacy_entity_rows(raw: object, path: Path) -> None:
    if not isinstance(raw, dict):
        return
    entities = raw.get("entities")
    if not isinstance(entities, dict):
        return
    for entity_id, row in entities.items():
        if not isinstance(row, dict):
            continue
        bind_values = row.get("bind_values")
        has_bind = isinstance(bind_values, dict) and bool(bind_values)
        has_legacy_top = ("name" in row and row.get("name")) or (
            "employer" in row and row.get("employer")
        )
        if has_legacy_top and not has_bind:
            raise LegacyEntitiesSchemaError(
                f"entities.json entity {entity_id!r} at {path} has legacy "
                f"top-level name/employer without bind_values. "
                f"Run: ./bin/refresh-example-network <network> --yes",
            )


class RegistryEntity(BaseModel):
    id: str
    bind_values: dict[str, str] = Field(default_factory=dict)
    validation_state: str = "provisional"
    field_states: dict[str, str] = Field(default_factory=dict)
    attr_sources: dict[str, str] = Field(
        default_factory=dict,
        description="Attr name → specialist category slug that stores the value.",
    )
    last_researched_at: dict[str, str] = Field(
        default_factory=dict,
        description="Attr name → ISO8601 UTC timestamp of last successful research write.",
    )
    source: str = "query_bind"
    created_at: str = ""

    def bind_value(self, field: str) -> str | None:
        raw = self.bind_values.get(field.strip().lower())
        if raw is None or not str(raw).strip():
            return None
        return str(raw).strip()


class EntitiesDocument(BaseModel):
    version: str = "1.0"
    last_updated: str = ""
    entities: dict[str, RegistryEntity] = Field(default_factory=dict)
    bind_index: dict[str, str] = Field(default_factory=dict)


def registry_entity_to_match(
    entity: RegistryEntity,
    *,
    mvr: MvrPolicy | None = None,
) -> dict[str, Any]:
    """Shape registry row for supervisor / response builders."""
    if mvr is None:
        from network.mvr import load_mvr

        mvr = load_mvr()
    out: dict[str, Any] = {
        "id": entity.id,
        "_registry": True,
        "_validation_state": entity.validation_state,
    }
    for field in mvr.bind_fields:
        key = field.strip().lower()
        if key:
            out[key] = entity.bind_value(key)
    return out


class EntityRegistry:
    """Load/save per-grain entity store with atomic writes."""

    def __init__(
        self,
        path: Path | None = None,
        *,
        grain: str | None = None,
        mvr: MvrPolicy | None = None,
        read_path: Path | None = None,
    ) -> None:
        from network.mvr import load_mvr

        if path is not None:
            self.grain = grain or "person"
            self._mvr = mvr or load_mvr(grain=self.grain)
            self.path = path
        else:
            store_path, self.grain = _resolve_registry_paths(grain or "")
            self._mvr = mvr or load_mvr(grain=self.grain)
            self.path = store_path
        if read_path is not None:
            self.path = read_path
        strategy_path, sqlite_path = _store_paths(self.path)
        self._store = EntityStore(
            self.grain,
            self.path,
            strategy_path,
            sqlite_path,
        )
        self._data = EntitiesDocument()
        self._field_indexes: dict[str, dict[str, list[str]]] = {}
        self._deferred_depth = 0
        self._load()

    def optimize_storage_threshold(self) -> int:
        raw = os.getenv("MYCELIUM_ENTITY_OPTIMIZE_STORAGE_THRESHOLD")
        if raw is None:
            raw = os.getenv("MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD", "50")
        try:
            return int(raw)
        except ValueError:
            return 50

    def optimize_storage(self) -> bool:
        if self._store.current_strategy() != "entities_document_v1":
            return False
        return self.entity_count() >= self.optimize_storage_threshold()

    def _maybe_optimize_storage(self) -> None:
        if not self.optimize_storage():
            return
        try:
            self._store.migrate_to("minisql_v1")
        except NotImplementedError:
            pass

    def _defer_flush(self) -> bool:
        return self._deferred_depth > 0 or _bootstrap_deferred_depth > 0

    @contextmanager
    def deferred_save(self) -> Iterator[EntityRegistry]:
        self._deferred_depth += 1
        try:
            yield self
        finally:
            self._deferred_depth -= 1
            if self._deferred_depth == 0:
                self.commit_deferred_save()

    def commit_deferred_save(self) -> None:
        self._maybe_optimize_storage()
        self._store.save(self._data)
        self._rebuild_field_indexes()

    def _rebuild_field_indexes(self) -> None:
        from agents.field_index import build_field_indexes

        self._field_indexes = build_field_indexes(
            self._data.entities,
            self._mvr.bind_fields,
        )

    def _load(self) -> None:
        try:
            self._data = self._store.load()
        except LegacyEntitiesSchemaError:
            raise
        except (OSError, json.JSONDecodeError, ValueError):
            self._data = EntitiesDocument()
        self._rebuild_field_indexes()

    def _save(self, *, rebuild_field_indexes: bool = True) -> None:
        if self._defer_flush():
            if rebuild_field_indexes:
                self._rebuild_field_indexes()
            return
        self._maybe_optimize_storage()
        self._store.save(self._data)
        if rebuild_field_indexes:
            self._rebuild_field_indexes()

    def reload(self) -> None:
        self._load()

    def lookup_by_target_lookup(self, lookup: dict[str, str]) -> list[str]:
        """AND-match registry rows by MVR bind fields (exact normalized index)."""
        from agents.field_index import intersect_lookup

        return intersect_lookup(
            self._field_indexes,
            lookup,
            self._mvr.bind_fields,
        )

    def field_indexes(self) -> dict[str, dict[str, list[str]]]:
        """Snapshot of in-memory per-field inverted indexes (tests/diagnostics)."""
        return {
            field: {value: list(ids) for value, ids in bucket.items()}
            for field, bucket in self._field_indexes.items()
        }

    def entity_count(self) -> int:
        return len(self._data.entities)

    def list_entities(self) -> list[RegistryEntity]:
        return list(self._data.entities.values())

    def _bind_fields(self) -> list[str]:
        return list(self._mvr.bind_fields)

    def lookup_by_bind_values(self, bind_values: dict[str, str]) -> RegistryEntity | None:
        bind_fields = self._bind_fields()
        key = make_bind_key(bind_values, bind_fields)
        entity_id = self._data.bind_index.get(key)
        if not entity_id:
            return None
        return self._data.entities.get(entity_id)

    def lookup_by_id(self, entity_id: str) -> RegistryEntity | None:
        return self._data.entities.get(entity_id)

    def lookup_by_field(self, field: str, value: str) -> list[RegistryEntity]:
        norm = normalize_field_index_value(value)
        if not norm:
            return []
        field_key = field.strip().lower()
        entity_ids = self._field_indexes.get(field_key, {}).get(norm, [])
        entities: list[RegistryEntity] = []
        for entity_id in entity_ids:
            entity = self._data.entities.get(entity_id)
            if entity is not None:
                entities.append(entity)
        return entities

    def assign_bind_index(self, entity_id: str, bind_values: dict[str, str]) -> None:
        bind_fields = self._bind_fields()
        self._data.bind_index[make_bind_key(bind_values, bind_fields)] = entity_id

    def add_bind_alias(self, entity_id: str, bind_values: dict[str, str]) -> None:
        """Attach another bind_index key to an existing entity (bootstrap aliases).

        Only ``bind_index`` changes; ``entity.bind_values`` stay the same, so field
        indexes are unchanged and ``lookup_by_bind_values`` resolves via the new key.
        """
        entity = self._data.entities.get(entity_id)
        if entity is None:
            raise ValueError(f"Unknown registry entity: {entity_id}")
        full = require_full_bind_values(
            {str(k).strip().lower(): str(v).strip() for k, v in bind_values.items()},
            self._bind_fields(),
        )
        self.assign_bind_index(entity_id, full)
        self._save(rebuild_field_indexes=False)

    def pop_bind_index(self, bind_values: dict[str, str]) -> None:
        bind_fields = self._bind_fields()
        self._data.bind_index.pop(make_bind_key(bind_values, bind_fields), None)

    def register_entity(self, entity: RegistryEntity) -> None:
        self._data.entities[entity.id] = entity

    def save_entity(self, entity: RegistryEntity) -> None:
        self._data.entities[entity.id] = entity
        self._save()

    def promote_validated(self, entity_id: str) -> RegistryEntity:
        """Promote provisional entity and MVR field states to validated."""
        entity = self._data.entities.get(entity_id)
        if entity is None:
            raise KeyError(f"Unknown registry entity: {entity_id}")
        entity.validation_state = "validated"
        entity.field_states = {
            field.strip().lower(): "validated"
            for field in self._mvr.bind_fields
            if field.strip()
        }
        self._save()
        return entity

    def record_research_attribution(
        self,
        entity_id: str,
        updates: dict[str, tuple[str, str]],
    ) -> RegistryEntity:
        """Merge attr_sources and last_researched_at for attrs researched this pass."""
        entity = self._data.entities.get(entity_id)
        if entity is None:
            raise KeyError(f"Unknown registry entity: {entity_id}")
        for attr, (category, researched_at) in updates.items():
            entity.attr_sources[attr] = category
            entity.last_researched_at[attr] = researched_at
        self._save()
        return entity


def get_entity_registry(*, grain: str | None = None) -> EntityRegistry:
    from network.mvr import default_mvr_grain

    resolved_grain = grain or default_mvr_grain()
    cached = _registry.get(resolved_grain)
    if cached is not None:
        return cached
    registry = EntityRegistry(grain=resolved_grain)
    _registry[resolved_grain] = registry
    return registry


def reset_entity_registry(*, grain: str | None = None) -> None:
    global _bootstrap_deferred_depth
    if grain is None:
        _registry.clear()
        _bootstrap_deferred_depth = 0
        return
    _registry.pop(grain, None)

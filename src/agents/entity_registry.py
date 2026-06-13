"""Runtime entity registry (``entities.json``) for provisional binds."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_registry: "EntityRegistry | None" = None


def _normalize_name_for_bind(name: str) -> str:
    text = name.strip().lower()
    for ch in ("'", "-", "\u2019"):
        text = text.replace(ch, "")
    return " ".join(text.split())


def _default_entities_path() -> Path:
    from network.paths import runtime_path

    return runtime_path("MYCELIUM_ENTITIES_PATH")


def make_bind_key(name: str, employer: str) -> str:
    """Normalized bind index key: ``lower(name)|lower(employer)``."""
    return (
        f"{_normalize_name_for_bind(name)}|"
        f"{_normalize_name_for_bind(employer)}"
    )


class RegistryEntity(BaseModel):
    id: str
    name: str
    employer: str | None = None
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


class EntitiesDocument(BaseModel):
    version: str = "1.0"
    last_updated: str = ""
    entities: dict[str, RegistryEntity] = Field(default_factory=dict)
    bind_index: dict[str, str] = Field(default_factory=dict)


def registry_entity_to_match(entity: RegistryEntity) -> dict[str, Any]:
    """Shape registry row for supervisor / response builders."""
    return {
        "id": entity.id,
        "name": entity.name,
        "employer": entity.employer,
        "_registry": True,
        "_validation_state": entity.validation_state,
    }


class EntityRegistry:
    """Load/save ``entities.json`` with atomic writes."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else _default_entities_path()
        self._data = EntitiesDocument()
        self._field_indexes: dict[str, dict[str, list[str]]] = {}
        self._load()

    def _rebuild_field_indexes(self) -> None:
        from agents.field_index import build_field_indexes
        from network.mvr import load_mvr

        mvr = load_mvr()
        self._field_indexes = build_field_indexes(
            self._data.entities,
            mvr.bind_fields,
        )

    def _load(self) -> None:
        if not self.path.is_file():
            self._data = EntitiesDocument()
            self._rebuild_field_indexes()
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = EntitiesDocument.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValueError):
            self._data = EntitiesDocument()
        self._rebuild_field_indexes()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data.last_updated = datetime.now(timezone.utc).isoformat()
        payload = self._data.model_dump_json(indent=2)
        fd, tmp_path = tempfile.mkstemp(
            dir=self.path.parent,
            suffix=".json.tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_path, self.path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        self._rebuild_field_indexes()

    def reload(self) -> None:
        self._load()

    def lookup_by_target_lookup(self, lookup: dict[str, str]) -> list[str]:
        """AND-match registry rows by MVR bind fields (exact normalized index)."""
        from agents.field_index import intersect_lookup
        from network.mvr import load_mvr

        return intersect_lookup(
            self._field_indexes,
            lookup,
            load_mvr().bind_fields,
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

    def lookup_by_bind_key(self, name: str, employer: str) -> RegistryEntity | None:
        key = make_bind_key(name, employer)
        entity_id = self._data.bind_index.get(key)
        if not entity_id:
            return None
        return self._data.entities.get(entity_id)

    def lookup_by_id(self, entity_id: str) -> RegistryEntity | None:
        return self._data.entities.get(entity_id)

    def lookup_by_name(self, name: str) -> list[RegistryEntity]:
        target = _normalize_name_for_bind(name)
        if not target:
            return []
        return [
            entity
            for entity in self._data.entities.values()
            if _normalize_name_for_bind(entity.name) == target
        ]

    def assign_bind_index(self, entity_id: str, name: str, employer: str) -> None:
        self._data.bind_index[make_bind_key(name, employer)] = entity_id

    def pop_bind_index(self, name: str, employer: str) -> None:
        self._data.bind_index.pop(make_bind_key(name, employer), None)

    def register_entity(self, entity: RegistryEntity) -> None:
        self._data.entities[entity.id] = entity

    def save_entity(self, entity: RegistryEntity) -> None:
        self._data.entities[entity.id] = entity
        self._save()

    def ensure_bound_entity(
        self,
        name: str,
        employer: str,
        *,
        source: str,
        validation_state: str,
    ) -> tuple[RegistryEntity, bool]:
        """Return entity for bind key; allocate uuid4 + persist if missing.

        The bool is True when an existing row was returned (duplicate bind).
        On hit, id/source/validation_state are not changed.
        """
        from agents.attribute_write import ensure_entity_bind

        return ensure_entity_bind(
            name,
            employer,
            source=source,
            validation_state=validation_state,
        )

    def bind_provisional(self, name: str, employer: str) -> tuple[RegistryEntity, bool]:
        """Create provisional entity or return existing row (duplicate bind)."""
        return self.ensure_bound_entity(
            name,
            employer,
            source="query_bind",
            validation_state="provisional",
        )

    def promote_validated(self, entity_id: str) -> RegistryEntity:
        """Promote provisional entity and MVR field states to validated."""
        entity = self._data.entities.get(entity_id)
        if entity is None:
            raise KeyError(f"Unknown registry entity: {entity_id}")
        entity.validation_state = "validated"
        entity.field_states = {
            "name": "validated",
            "employer": "validated",
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


def get_entity_registry() -> EntityRegistry:
    global _registry
    if _registry is None:
        _registry = EntityRegistry()
    return _registry


def reset_entity_registry() -> None:
    global _registry
    _registry = None

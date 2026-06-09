"""Runtime entity registry (``entities.json``) for provisional binds."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
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
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            self._data = EntitiesDocument()
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = EntitiesDocument.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValueError):
            self._data = EntitiesDocument()

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

    def reload(self) -> None:
        self._load()

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

    def bind_provisional(self, name: str, employer: str) -> tuple[RegistryEntity, bool]:
        """Create provisional entity or return existing row (duplicate bind)."""
        key = make_bind_key(name, employer)
        existing_id = self._data.bind_index.get(key)
        if existing_id:
            existing = self._data.entities.get(existing_id)
            if existing is not None:
                return existing, True

        now = datetime.now(timezone.utc).isoformat()
        entity_id = str(uuid.uuid4())
        entity = RegistryEntity(
            id=entity_id,
            name=name.strip(),
            employer=employer.strip(),
            validation_state="provisional",
            field_states={"name": "provisional", "employer": "provisional"},
            source="query_bind",
            created_at=now,
        )
        self._data.entities[entity_id] = entity
        self._data.bind_index[key] = entity_id
        self._save()
        return entity, False


def get_entity_registry() -> EntityRegistry:
    global _registry
    if _registry is None:
        _registry = EntityRegistry()
    return _registry


def reset_entity_registry() -> None:
    global _registry
    _registry = None

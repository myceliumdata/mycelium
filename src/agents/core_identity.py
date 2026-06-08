"""Core Identity facade (Phase 1 storage adapter).

``CoreDataAgent`` (``agents.core_data``) performs lookups via ``get_core_identity()``.
This module remains the thin persistence facade over ``storage.core`` until core data
logic fully lives in the specialist node.
"""

from __future__ import annotations

from models.state import SeedRecord
from storage.core import CoreStorage, get_storage


class CoreIdentity:
    """Agent responsible for the system's core person identity data (id, name, employer)."""

    def __init__(self, storage: CoreStorage | None = None) -> None:
        self._storage = storage

    def _resolve_storage(self) -> CoreStorage:
        return self._storage if self._storage is not None else get_storage()

    def find_by_key(self, entity_key: str) -> list[SeedRecord]:
        """Resolve zero or more seed records by id or name (case-insensitive name match)."""
        return self._resolve_storage().find_persons(entity_key)

    def persist(self, record: SeedRecord) -> None:
        """Upsert a validated core seed record."""
        self._resolve_storage().upsert_person(record)


_core_identity: CoreIdentity | None = None


def get_core_identity() -> CoreIdentity:
    """Return the process-wide Core Identity agent."""
    global _core_identity
    if _core_identity is None:
        _core_identity = CoreIdentity()
    return _core_identity


def reset_core_identity() -> None:
    """Clear Core Identity singleton (for tests)."""
    global _core_identity
    _core_identity = None

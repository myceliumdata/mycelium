"""Core Identity agent (Phase 1).

The supervisor routes lookup and ingest persistence through Core Identity rather than
calling ``get_storage()`` directly. A dedicated specialist implementation may replace
this module in a later phase.
"""

from __future__ import annotations

from models.state import Person
from storage.core import CoreStorage, get_storage


class CoreIdentity:
    """Agent responsible for the system's core person identity data (id, name, employer)."""

    def __init__(self, storage: CoreStorage | None = None) -> None:
        self._storage = storage

    def _resolve_storage(self) -> CoreStorage:
        return self._storage if self._storage is not None else get_storage()

    def find_by_key(self, person_key: str) -> Person | None:
        """Resolve a person by id or name (case-insensitive name match)."""
        return self._resolve_storage().find_person(person_key)

    def persist(self, person: Person) -> None:
        """Upsert a validated core person record."""
        self._resolve_storage().upsert_person(person)


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

"""Core identity access facade (Phase 1).

The supervisor routes lookup and ingest persistence through this module instead of
calling ``get_storage()`` directly. A dedicated Core Identity specialist agent may
replace this facade in a later phase.
"""

from __future__ import annotations

from models.state import Person
from storage.core import CoreStorage, get_storage


class CoreIdentityAccessor:
    """Thin adapter over core ``people`` storage for identity resolution and writes."""

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


_accessor: CoreIdentityAccessor | None = None


def get_core_identity() -> CoreIdentityAccessor:
    """Return the process-wide core identity accessor."""
    global _accessor
    if _accessor is None:
        _accessor = CoreIdentityAccessor()
    return _accessor


def reset_core_identity() -> None:
    """Clear accessor singleton (for tests)."""
    global _accessor
    _accessor = None

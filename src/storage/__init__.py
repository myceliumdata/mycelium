"""SQLite path bootstrap (``mycelium.db``); identity is in ``entities.json``."""

from storage.core import CoreStorage, get_storage

__all__ = ["CoreStorage", "get_storage"]

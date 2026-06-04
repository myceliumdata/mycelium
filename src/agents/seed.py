"""Direct JSON seed loader for the seed-data-context redesign.

The committed ``data/seed.json`` is the read-only origin of person records
(name + employer only; no legacy ``id`` in the file — see ``data/prepare_seed.py``).
Stable ``id`` (UUID, uuid5 from name|employer) is assigned at load time and is
never written back into the static JSON. Supervisor and tests resolve people by
name or ``id`` via :func:`find_by_key`.

People seeding no longer flows through SQLite; see :mod:`storage.core` for
checkpoints/history only in this phase.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# TODO (future phase): richer person ID strategies, attached provenance/validation,
# support for seed file with pre-assigned UUIDs, cross-specialist peer retrieval
# instead of supervisor context fan-out.

DEFAULT_SEED_PATH = Path("data/seed.json")
_ID_NAMESPACE = uuid.NAMESPACE_DNS
_ID_PREFIX = "mycelium-seed-v1:"


def _default_seed_path() -> Path:
    return Path(os.getenv("MYCELIUM_SEED_PATH", str(DEFAULT_SEED_PATH)))


def _assign_id(record: dict[str, Any]) -> str:
    """Stable UUID for a seed row (name|employer); does not mutate the JSON file."""
    base = f"{record.get('name', '')}|{record.get('employer', '')}"
    return str(uuid.uuid5(_ID_NAMESPACE, f"{_ID_PREFIX}{base}"))


def _enrich_person(record: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(record)
    enriched["id"] = _assign_id(record)
    return enriched


@dataclass
class SeedData:
    """Loaded seed with enriched person records."""

    people: list[dict[str, Any]] = field(default_factory=list)
    by_id: dict[str, dict[str, Any]] = field(default_factory=dict)

    def reload_from_path(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Seed file not found: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_people = payload.get("people", [])
        self.people = [_enrich_person(row) for row in raw_people]
        self.by_id = {p["id"]: p for p in self.people}


_seed_data: SeedData | None = None


def get_seed_data() -> SeedData:
    """Return cached seed data, loading from disk on first access."""
    global _seed_data
    if _seed_data is None:
        data = SeedData()
        data.reload_from_path(_default_seed_path())
        _seed_data = data
    return _seed_data


def reset_seed_data() -> None:
    """Clear cached seed (for tests and env changes)."""
    global _seed_data
    _seed_data = None


def find_by_key(person_key: str) -> list[dict[str, Any]]:
    """Resolve by ``id`` UUID or exact name (case-insensitive).

    UUID match returns zero or one record. Name match may return multiple
    records when the same name appears with different employers.
    """
    key = person_key.strip()
    if not key:
        return []

    data = get_seed_data()
    if key in data.by_id:
        return [data.by_id[key]]

    key_lower = key.lower()
    return [p for p in data.people if (p.get("name") or "").lower() == key_lower]

"""Direct JSON seed loader for the seed-data-context redesign.

Each network's ``seed.json`` under ``network_root`` is the read-only origin of
person records (name + employer only; no legacy ``id`` in the file). The CRM
example lives at ``examples/networks/crm/seed.json``.

At load time each row is mirrored into ``entities.json`` via
:meth:`EntityRegistry.ensure_bound_entity` (uuid4, ``source: seed_bootstrap``).
IDs persist in the registry ``bind_index`` so MCP per-query seed reload keeps
stable foreign keys for specialist storage. Supervisor and tests resolve people
by name or ``id`` via :func:`find_by_key`.

People seeding no longer flows through SQLite; see :mod:`storage.core` for
checkpoints/history only in this phase.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# TODO (future phase): richer person ID strategies, attached provenance/validation,
# support for seed file with pre-assigned UUIDs, cross-specialist peer retrieval
# instead of supervisor context fan-out.


def _default_seed_path() -> Path:
    from network.paths import runtime_path

    return runtime_path("MYCELIUM_SEED_PATH")


def _enrich_person(record: dict[str, Any]) -> dict[str, Any]:
    """Attach registry-backed uuid4 id for a seed row."""
    from agents.entity_registry import get_entity_registry

    enriched = dict(record)
    name = str(record.get("name") or "").strip()
    employer = str(record.get("employer") or "").strip()
    entity, _ = get_entity_registry().ensure_bound_entity(
        name,
        employer,
        source="seed_bootstrap",
        validation_state="validated",
    )
    enriched["id"] = entity.id
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


def find_by_key(entity_key: str) -> list[dict[str, Any]]:
    """Resolve by ``id`` UUID or exact name (case-insensitive).

    UUID match returns zero or one record. Name match may return multiple
    records when the same name appears with different employers.
    """
    key = entity_key.strip()
    if not key:
        return []

    data = get_seed_data()
    if key in data.by_id:
        return [data.by_id[key]]

    key_lower = key.lower()
    return [p for p in data.people if (p.get("name") or "").lower() == key_lower]

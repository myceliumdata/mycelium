"""Person record preparation helpers (unwired legacy).

Used only by the legacy enrich module; reserved for future internal addition flows.
"""

from __future__ import annotations

from uuid import uuid4

from models.state import Person


def ensure_id(person: Person) -> Person:
    """Assign a stable id when preparing a new core record (legacy addition path)."""
    if person.id:
        return person
    slug = person.name.lower().replace(" ", "-")
    return person.model_copy(update={"id": f"person-{slug}-{uuid4().hex[:6]}"})

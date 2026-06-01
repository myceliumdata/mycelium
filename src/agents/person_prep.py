"""Person record preparation helpers used by ingest-path agents."""

from __future__ import annotations

from uuid import uuid4

from models.state import Person


def ensure_person_id(person: Person) -> Person:
    """Assign a stable id when ingesting new records."""
    if person.id:
        return person
    slug = person.name.lower().replace(" ", "-")
    return person.model_copy(update={"id": f"person-{slug}-{uuid4().hex[:6]}"})

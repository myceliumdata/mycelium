"""Person record preparation helpers (unwired legacy).

Used only by the legacy enrich module; reserved for future internal addition flows.
"""

from __future__ import annotations

from uuid import uuid4

from models.state import IdentityRecord


def ensure_id(record: IdentityRecord) -> IdentityRecord:
    """Assign a stable id when preparing a new core record (legacy addition path)."""
    if record.id:
        return record
    slug = record.name.lower().replace(" ", "-")
    return record.model_copy(update={"id": f"record-{slug}-{uuid4().hex[:6]}"})

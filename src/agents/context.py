"""Build full person context: seed records + union of all specialist storage (by person_id).

TODO: Eventually specialists should retrieve context from peer agents instead of the
supervisor assembling and passing the full union on every invocation.
"""

from __future__ import annotations

from typing import Any

from agents.registry import get_agent_registry
from agents.seed import get_seed_data
from agents.specialists.base import SpecialistStorage


def reset_context_builder() -> None:
    """No-op reset for test symmetry with other singletons."""
    return None


def get_context_builder() -> "ContextBuilder":
    return ContextBuilder()


class ContextBuilder:
    """Synchronous context assembly from seed loader + specialist JSON stores."""

    def build_full_context(
        self,
        person_ids: list[str],
        *,
        seed_records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if seed_records is not None:
            seed_part: Any = (
                seed_records[0] if len(seed_records) == 1 else seed_records
            )
        else:
            data = get_seed_data()
            by_id = {p["person_id"]: p for p in data.people if p.get("person_id")}
            selected = [by_id[pid] for pid in person_ids if pid in by_id]
            seed_part = selected[0] if len(selected) == 1 else selected

        specialist_part: dict[str, Any] = {}
        registry = get_agent_registry()
        for agent in registry.list_agents():
            if not agent.get("is_generated"):
                continue
            category = agent.get("category")
            if not category:
                continue
            try:
                store = SpecialistStorage(category=category)
                payload = store.load()
                records = payload.get("records", {})
                cat_slice: dict[str, Any] = {}
                for pid in person_ids:
                    if pid in records:
                        cat_slice[pid] = records[pid]
                if cat_slice:
                    specialist_part[category] = cat_slice
            except OSError:
                continue

        return {"seed": seed_part, "specialists": specialist_part}

"""Research gate: specialists/Tavily only on validated or seed entities (Slice 6)."""

from __future__ import annotations

from typing import Any

from models.state import MyceliumGraphState, normalized_requested_attributes

RESEARCH_GATE_MESSAGE = (
    "Record is provisionally bound; core validation must complete before "
    "researching requested attributes."
)


def research_gate_allows(
    *,
    current_id: str | None,
    matched: list[dict[str, Any]],
) -> bool:
    """True when attribute research may invoke specialists."""
    if not matched:
        return False
    if len(matched) != 1:
        return not matched[0].get("_registry")
    rec = matched[0]
    entity_id = current_id or rec.get("id")
    if not entity_id:
        return False
    if rec.get("_registry"):
        return rec.get("_validation_state") == "validated"
    return True


def is_research_gated(state: MyceliumGraphState) -> bool:
    """True when attrs were requested but the gate blocks specialist research."""
    requested = normalized_requested_attributes(state.query.requested_attributes)
    if not requested:
        return False
    matched = state.matched_records or []
    if not matched:
        return False
    if state.validation_passed is False:
        return False
    return not research_gate_allows(
        current_id=state.current_id,
        matched=matched,
    )

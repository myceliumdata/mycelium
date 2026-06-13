"""Research gate: specialists/Tavily only on validated registry entities (Slice 6)."""

from __future__ import annotations

from typing import Any

from models.state import MyceliumGraphState, graph_requested_attributes

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
    _ = current_id
    if not matched:
        return False
    return all(rec.get("_validation_state") == "validated" for rec in matched)


def is_research_gated(state: MyceliumGraphState) -> bool:
    """True when attrs were requested but the gate blocks specialist research."""
    requested = graph_requested_attributes(state)
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

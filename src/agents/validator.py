"""Validator agent (unwired legacy).

Reserved for future internal data-addition coordination. Not imported by
``agents.__init__`` or ``graphs.core``. Do not use from public CLI/MCP paths.
"""

from __future__ import annotations

import re
from typing import Any

from models.state import MyceliumGraphState

# Legacy ingest validator (unwired); kept local to avoid reviving removed state constants.
_MINIMUM_VIABLE_FIELDS = ["name", "employer"]

_NAME_PATTERN = re.compile(r"^[\w\s\.\-'’,]{2,}$", re.UNICODE)


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


async def validator_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Validate minimum viable core CRM fields before supervisor finalizes response."""
    current = _coerce(state)
    person = current.person
    errors: list[str] = []

    if person is None:
        errors.append("ValidatorAgent: person record missing.")
    else:
        for field in _MINIMUM_VIABLE_FIELDS:
            value = getattr(person, field, None)
            if not value or not str(value).strip():
                errors.append(f"ValidatorAgent: required field '{field}' is empty.")

        if person.name and not _NAME_PATTERN.match(person.name.strip()):
            errors.append("ValidatorAgent: name format is invalid.")

    passed = len(errors) == 0
    outcome = "passed" if passed else "failed"

    return {
        "validation_passed": passed,
        "validation_errors": errors,
        "audit_log": [f"ValidatorAgent: validation {outcome}."],
    }

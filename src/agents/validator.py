"""Validator agent: basic structural validation for core person records."""

from __future__ import annotations

import re
from typing import Any

from models.state import MINIMUM_VIABLE_FIELDS, MyceliumGraphState

_NAME_PATTERN = re.compile(r"^[\w\s\.\-'’,]{2,}$", re.UNICODE)


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def validator_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """Validate minimum viable core CRM fields before supervisor finalizes response."""
    current = _coerce(state)
    person = current.person
    errors: list[str] = []

    if person is None:
        errors.append("ValidatorAgent: person record missing.")
    else:
        for field in MINIMUM_VIABLE_FIELDS:
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

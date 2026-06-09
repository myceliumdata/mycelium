"""Rule-based MVR validation for provisional registry entities (Slice 5)."""

from __future__ import annotations

from typing import Any, Literal

ValidationStatus = Literal["pass", "fail", "pending"]


def _validate_name(name: str) -> dict[str, Any]:
    text = name.strip()
    if len(text) < 2:
        return {
            "field": "name",
            "status": "fail",
            "reason": "name must be at least 2 characters",
        }
    if text.isdigit():
        return {
            "field": "name",
            "status": "fail",
            "reason": "name cannot be all digits",
        }
    return {"field": "name", "status": "pass"}


def _validate_employer(employer: str | None) -> dict[str, Any]:
    text = (employer or "").strip()
    if len(text) < 2:
        return {
            "field": "employer",
            "status": "fail",
            "reason": "employer must be at least 2 characters",
        }
    return {"field": "employer", "status": "pass"}


_MVR_VALIDATORS: tuple[tuple[str, str, Any], ...] = (
    ("name", "demographic_specialist", _validate_name),
    ("employer", "professional_specialist", _validate_employer),
)


def run_mvr_validation(name: str, employer: str | None) -> list[dict[str, Any]]:
    """Run demographic + professional rule checks; return validation_contrib rows."""
    contribs: list[dict[str, Any]] = []
    for field, agent, validator in _MVR_VALIDATORS:
        if field == "name":
            result = validator(name)
        else:
            result = validator(employer)
        contribs.append(
            {
                "agent": agent,
                "validation_contrib": {
                    "field": result["field"],
                    "status": result["status"],
                    **(
                        {"reason": result["reason"]}
                        if result.get("reason")
                        else {}
                    ),
                },
            },
        )
    return contribs


def validation_all_passed(contribs: list[dict[str, Any]]) -> bool:
    for item in contribs:
        vc = item.get("validation_contrib") or {}
        if vc.get("status") != "pass":
            return False
    return bool(contribs)


def validation_failure_summary(contribs: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in contribs:
        vc = item.get("validation_contrib") or {}
        if vc.get("status") == "fail":
            field = vc.get("field", "field")
            reason = vc.get("reason") or "failed validation"
            parts.append(f"{field}: {reason}")
    return "; ".join(parts) if parts else "validation failed"

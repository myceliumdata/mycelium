"""Rule-based MVR validation for provisional registry entities (Slice 5).

Validators run inline in ``validate_entity_node`` — attribute specialists are not
invoked during validation (Pattern C / specialist-driven validation deferred).
"""

from __future__ import annotations

from typing import Any, Literal

from agents.attribute_write import resolve_attribute_owner
from agents.entity_registry import RegistryEntity

ValidationStatus = Literal["pass", "fail", "pending"]


def _validate_bind_string(field: str, value: str | None) -> dict[str, Any]:
    text = (value or "").strip()
    if len(text) < 2:
        return {
            "field": field,
            "status": "fail",
            "reason": f"{field} must be at least 2 characters",
        }
    if text.isdigit():
        return {
            "field": field,
            "status": "fail",
            "reason": f"{field} cannot be all digits",
        }
    return {"field": field, "status": "pass"}


def run_mvr_validation(
    entity: RegistryEntity,
    *,
    mvr: Any | None = None,
) -> list[dict[str, Any]]:
    """Run rule checks for each active MVR bind field; return validation_contrib rows."""
    from network.mvr import load_mvr

    policy = mvr if mvr is not None else load_mvr()
    contribs: list[dict[str, Any]] = []
    for raw_field in policy.bind_fields:
        field = raw_field.strip().lower()
        if not field:
            continue
        result = _validate_bind_string(field, entity.bind_value(field))
        _, agent = resolve_attribute_owner(field)
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

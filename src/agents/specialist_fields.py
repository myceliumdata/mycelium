"""Versioned provenance helpers for specialist extended-attribute storage."""

from __future__ import annotations

from typing import Any

_FLAT_V1_ERROR = (
    "Storage uses deprecated flat field format; refresh the network or delete "
    "agents/<category>/storage.json."
)


def is_versioned_field(entry: Any) -> bool:
    """True when entry uses versioned_provenance_v1 shape."""
    return isinstance(entry, dict) and "versions" in entry


def _is_flat_v1_field(entry: dict[str, Any]) -> bool:
    return "status" in entry and "versions" not in entry


def validate_versioned_field(
    entry: Any,
    *,
    field_name: str,
    category: str,
) -> None:
    """Fail loud on deprecated flat v1 field blobs."""
    _ = field_name, category
    if isinstance(entry, dict) and _is_flat_v1_field(entry):
        raise ValueError(_FLAT_V1_ERROR)


def empty_versioned_entry() -> dict[str, Any]:
    return {"versions": [], "current_version_id": None}


def next_version_id(entry: dict[str, Any] | None) -> str:
    if not entry or not entry.get("versions"):
        return "v1"
    max_n = 0
    for version in entry.get("versions") or []:
        if not isinstance(version, dict):
            continue
        vid = str(version.get("id") or "")
        if vid.startswith("v") and vid[1:].isdigit():
            max_n = max(max_n, int(vid[1:]))
    return f"v{max_n + 1}" if max_n else "v1"


def current_version(entry: Any) -> dict[str, Any] | None:
    if not isinstance(entry, dict) or not is_versioned_field(entry):
        return None
    versions = entry.get("versions") or []
    if not versions:
        return None
    current_id = entry.get("current_version_id")
    if current_id:
        for version in versions:
            if isinstance(version, dict) and version.get("id") == current_id:
                return version
    last = versions[-1]
    return last if isinstance(last, dict) else None


def current_status(entry: Any) -> str:
    version = current_version(entry)
    if version is None:
        return "empty"
    return str(version.get("status") or "empty")


def current_value(entry: Any) -> str | None:
    version = current_version(entry)
    if version is None or version.get("status") != "found":
        return None
    raw = version.get("value")
    return str(raw) if raw is not None else None


def field_has_value(entry: Any) -> bool:
    if not isinstance(entry, dict) or not is_versioned_field(entry):
        return False
    status = current_status(entry)
    if status in ("pending", "na", "empty"):
        return False
    return status == "found" and bool(current_value(entry))


def field_is_pending(entry: Any) -> bool:
    return isinstance(entry, dict) and is_versioned_field(entry) and current_status(entry) == "pending"


def pending_last_error(entry: Any) -> str:
    if not isinstance(entry, dict) or not is_versioned_field(entry):
        return ""
    version = current_version(entry)
    return str((version or {}).get("last_error") or "")


def pending_started_at_raw(entry: Any) -> str | None:
    if not isinstance(entry, dict) or not is_versioned_field(entry):
        return None
    version = current_version(entry)
    raw = (version or {}).get("started_at") or (version or {}).get("at")
    return str(raw) if raw else None


def field_is_na(entry: Any) -> bool:
    return isinstance(entry, dict) and is_versioned_field(entry) and current_status(entry) == "na"


def field_display_value(entry: Any) -> str:
    if not isinstance(entry, dict) or not is_versioned_field(entry):
        return str(entry) if entry is not None else ""
    status = current_status(entry)
    if status == "na":
        return "N/A"
    if status == "pending":
        return "pending"
    value = current_value(entry)
    return value if value is not None else status


def append_version(entry: dict[str, Any] | None, version_body: dict[str, Any]) -> dict[str, Any]:
    """Append a version and set current_version_id."""
    base = dict(entry) if isinstance(entry, dict) and is_versioned_field(entry) else empty_versioned_entry()
    versions = list(base.get("versions") or [])
    version = dict(version_body)
    if "id" not in version:
        version["id"] = next_version_id(base)
    versions.append(version)
    base["versions"] = versions
    base["current_version_id"] = version["id"]
    return base


def update_current_pending(
    entry: dict[str, Any],
    *,
    at: str,
    last_error: str,
) -> dict[str, Any]:
    """In-place update of the current pending version (P1-11 retry)."""
    version = current_version(entry)
    if version is None or version.get("status") != "pending":
        return entry
    updated = dict(entry)
    versions = []
    for item in updated.get("versions") or []:
        if isinstance(item, dict) and item.get("id") == version.get("id"):
            patched = dict(item)
            patched["at"] = at
            patched["last_error"] = last_error
            if "started_at" not in patched:
                patched["started_at"] = at
            versions.append(patched)
        else:
            versions.append(item)
    updated["versions"] = versions
    return updated


def ensure_versioned_for_write(entry: Any) -> dict[str, Any]:
    """Normalize storage entry for research writes.

    Legacy flat **pending** blobs (pre-versioned networks mid-research) are wrapped
    into a single ``v1`` pending version so P1-11 retry gates can update in place.
    Other flat v1 shapes fail loud via ``validate_versioned_field``.
    """
    if entry is None:
        return empty_versioned_entry()
    if isinstance(entry, dict) and is_versioned_field(entry):
        return dict(entry)
    if isinstance(entry, dict) and _is_flat_v1_field(entry):
        if entry.get("status") == "pending":
            now_at = str(entry.get("started_at") or entry.get("at") or "")
            body: dict[str, Any] = {
                "id": "v1",
                "at": now_at,
                "status": "pending",
                "started_at": entry.get("started_at") or now_at,
                "last_error": entry.get("last_error", ""),
            }
            return {
                "current_version_id": "v1",
                "versions": [body],
            }
        validate_versioned_field(entry, field_name="field", category="unknown")
    return empty_versioned_entry()


def research_actor(*, category: str, specialist_name: str) -> dict[str, str]:
    return {
        "kind": "research",
        "category": category,
        "specialist": specialist_name,
    }

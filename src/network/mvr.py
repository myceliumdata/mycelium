"""Minimum viable record (MVR) policy from ``network.json``."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from network.paths import NetworkPaths, resolve_network_root

_DEFAULT_BIND_FIELDS = ["name", "employer"]
_DEFAULT_DESCRIPTION = (
    "CRM people: display name plus current employer before bind and research."
)


@dataclass(frozen=True)
class MvrPolicy:
    """Per-network bind requirements before entity research (Slice 3)."""

    bind_fields: list[str]
    description: str

    def summary(self) -> dict[str, Any]:
        return {
            "bind_fields": list(self.bind_fields),
            "description": self.description,
        }


def _crm_default_mvr() -> MvrPolicy:
    return MvrPolicy(
        bind_fields=list(_DEFAULT_BIND_FIELDS),
        description=_DEFAULT_DESCRIPTION,
    )


def _parse_mvr_block(raw: Any) -> MvrPolicy | None:
    if not isinstance(raw, dict):
        return None
    bind_fields = raw.get("bind_fields")
    if not isinstance(bind_fields, list) or not bind_fields:
        return None
    fields = [str(item).strip() for item in bind_fields if str(item).strip()]
    if not fields:
        return None
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        description = _DEFAULT_DESCRIPTION
    return MvrPolicy(
        bind_fields=fields,
        description=description.strip(),
    )


def _is_uuid_shaped(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def legacy_entity_lookup_map(
    entity_key: str,
    binding: dict[str, str] | None = None,
    *,
    mvr: MvrPolicy | None = None,
) -> dict[str, str]:
    """Build a target-style lookup map from legacy ``EntityQuery`` fields."""
    policy = mvr if mvr is not None else load_mvr()
    allowed = {field.strip().lower() for field in policy.bind_fields if field.strip()}
    lookup: dict[str, str] = {}
    key = entity_key.strip()
    if key and not _is_uuid_shaped(key) and "name" in allowed:
        lookup["name"] = key
    for field, value in (binding or {}).items():
        field_key = field.strip().lower()
        text = value.strip() if isinstance(value, str) else ""
        if field_key in allowed and text:
            lookup[field_key] = text
    return lookup


def normalized_lookup_values(lookup: dict[str, str]) -> dict[str, str]:
    """Map lookup keys to lower-case bind field names with stripped values."""
    normalized: dict[str, str] = {}
    for key, value in lookup.items():
        field = key.strip().lower()
        if not field:
            continue
        text = value.strip() if isinstance(value, str) else ""
        if text:
            normalized[field] = text
    return normalized


def is_full_mvr_lookup(lookup: dict[str, str], mvr: MvrPolicy) -> bool:
    """True when lookup supplies every MVR bind field with a non-empty value.

    Empty strings and whitespace-only values are ignored (treated as absent).
    """
    required = {field.strip().lower() for field in mvr.bind_fields if field.strip()}
    provided = set(normalized_lookup_values(lookup).keys())
    return required.issubset(provided)


def can_create_on_zero_matches(
    lookup: dict[str, str],
    requested_attributes: list[str] | None = None,
    *,
    mvr: MvrPolicy | None = None,
) -> bool:
    """True when 0-match lookup may create on step-2 deliver (full MVR in lookup)."""
    _ = requested_attributes
    policy = mvr if mvr is not None else load_mvr()
    return is_full_mvr_lookup(lookup, policy)


def missing_mvr_bind_fields(
    lookup: dict[str, str],
    *,
    mvr: MvrPolicy | None = None,
) -> list[str]:
    """MVR bind fields absent from a normalized lookup (for lookup_incomplete)."""
    policy = mvr if mvr is not None else load_mvr()
    required = [field.strip().lower() for field in policy.bind_fields if field.strip()]
    provided = set(normalized_lookup_values(lookup).keys())
    return [field for field in required if field not in provided]


def load_mvr(*, paths: NetworkPaths | None = None) -> MvrPolicy:
    """Load MVR policy from ``network.json``; CRM default when ``mvr`` is absent."""
    if paths is None:
        root = resolve_network_root()
        paths = NetworkPaths.from_root(root)

    network_json = paths.root / "network.json"
    if not network_json.is_file():
        return _crm_default_mvr()

    try:
        data = json.loads(network_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _crm_default_mvr()

    if not isinstance(data, dict):
        return _crm_default_mvr()

    parsed = _parse_mvr_block(data.get("mvr"))
    return parsed if parsed is not None else _crm_default_mvr()

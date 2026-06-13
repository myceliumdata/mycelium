"""Minimum viable record (MVR) policy from ``network.json``."""

from __future__ import annotations

import json
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

    def allowed_binding_keys(self) -> set[str]:
        """MVR bind field keys accepted in ``EntityQuery.binding`` (legacy)."""
        return {field.strip().lower() for field in self.bind_fields if field.strip()}

    def required_fields_for_entity_key(self, entity_key: str) -> list[str]:
        """Return MVR bind fields not satisfied by the current query."""
        return self.required_bind_fields(entity_key, {})

    def required_bind_fields(
        self,
        entity_key: str,
        binding: dict[str, str],
    ) -> list[str]:
        """Return MVR bind fields not yet satisfied by entity_key + binding."""
        satisfied: set[str] = set()
        if entity_key.strip():
            satisfied.add("name")
        for field, value in binding.items():
            if value.strip():
                satisfied.add(field.strip().lower())
        return [field for field in self.bind_fields if field not in satisfied]

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


def normalize_binding(
    binding: dict[str, str] | None,
    mvr: MvrPolicy,
) -> dict[str, str]:
    """Strip binding to allowed MVR keys with non-empty values (ignore unknown keys)."""
    allowed = mvr.allowed_binding_keys()
    normalized: dict[str, str] = {}
    for key, value in (binding or {}).items():
        field = key.strip().lower()
        if field not in allowed:
            continue
        text = value.strip() if isinstance(value, str) else ""
        if text:
            normalized[field] = text
    return normalized


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

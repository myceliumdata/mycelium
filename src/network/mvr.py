"""Minimum viable record (MVR) policy from ``network.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from network.paths import NetworkPaths, resolve_network_root

_DEFAULT_BIND_FIELDS = ["name", "employer"]
_DEFAULT_NAME_SOURCE = "entity_key"
_DEFAULT_DESCRIPTION = (
    "CRM people: display name plus current employer before bind and research."
)


@dataclass(frozen=True)
class MvrPolicy:
    """Per-network bind requirements before entity research (Slice 3)."""

    bind_fields: list[str]
    name_source: str
    description: str

    def allowed_binding_keys(self) -> set[str]:
        """MVR bind field keys accepted in ``EntityQuery.binding``."""
        allowed = {field.strip().lower() for field in self.bind_fields if field.strip()}
        if self.name_source == "entity_key":
            allowed.discard("name")
        return allowed

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
        if self.name_source == "entity_key" and entity_key.strip():
            satisfied.add("name")
        for field, value in binding.items():
            if value.strip():
                satisfied.add(field.strip().lower())
        return [field for field in self.bind_fields if field not in satisfied]

    def summary(self) -> dict[str, Any]:
        return {
            "bind_fields": list(self.bind_fields),
            "name_source": self.name_source,
            "description": self.description,
        }


def _crm_default_mvr() -> MvrPolicy:
    return MvrPolicy(
        bind_fields=list(_DEFAULT_BIND_FIELDS),
        name_source=_DEFAULT_NAME_SOURCE,
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
    name_source = raw.get("name_source")
    if not isinstance(name_source, str) or not name_source.strip():
        name_source = _DEFAULT_NAME_SOURCE
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        description = _DEFAULT_DESCRIPTION
    return MvrPolicy(
        bind_fields=fields,
        name_source=name_source.strip(),
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

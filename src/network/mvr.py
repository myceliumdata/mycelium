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

    def summary(self) -> dict[str, Any]:
        return {
            "bind_fields": list(self.bind_fields),
            "description": self.description,
        }


@dataclass(frozen=True)
class GrainMvrPolicy:
    """Per-grain MVR policy plus entity store path relative to network root."""

    bind_fields: list[str]
    description: str
    entities_file: str

    def to_mvr_policy(self) -> MvrPolicy:
        return MvrPolicy(
            bind_fields=list(self.bind_fields),
            description=self.description,
        )

    def summary(self) -> dict[str, Any]:
        return {
            "bind_fields": list(self.bind_fields),
            "description": self.description,
            "entities_file": self.entities_file,
        }


@dataclass(frozen=True)
class NetworkMvrConfig:
    """Multi-grain MVR configuration from ``network.json``."""

    default_grain: str
    grains: dict[str, GrainMvrPolicy]

    def summary(self) -> dict[str, Any]:
        return {
            "default_grain": self.default_grain,
            "grains": {
                name: grain.summary() for name, grain in self.grains.items()
            },
        }


def _crm_default_mvr() -> MvrPolicy:
    return MvrPolicy(
        bind_fields=list(_DEFAULT_BIND_FIELDS),
        description=_DEFAULT_DESCRIPTION,
    )


def _crm_default_config() -> NetworkMvrConfig:
    policy = _crm_default_mvr()
    grain = GrainMvrPolicy(
        bind_fields=policy.bind_fields,
        description=policy.description,
        entities_file="entities/person.json",
    )
    return NetworkMvrConfig(default_grain="person", grains={"person": grain})


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


def _parse_grains_block(mvr_raw: dict[str, Any]) -> dict[str, GrainMvrPolicy] | None:
    grains_raw = mvr_raw.get("grains")
    if not isinstance(grains_raw, dict) or not grains_raw:
        return None
    grains: dict[str, GrainMvrPolicy] = {}
    for grain_name, grain_raw in grains_raw.items():
        name = str(grain_name).strip()
        if not name:
            continue
        if not isinstance(grain_raw, dict):
            raise ValueError(f"network.json mvr.grains.{name} must be an object")
        policy = _parse_mvr_block(grain_raw)
        if policy is None:
            raise ValueError(
                f"network.json mvr.grains.{name} requires non-empty bind_fields",
            )
        entities_file_raw = grain_raw.get("entities_file")
        if isinstance(entities_file_raw, str) and entities_file_raw.strip():
            entities_file = entities_file_raw.strip()
        else:
            entities_file = f"entities/{name}.json"
        grains[name] = GrainMvrPolicy(
            bind_fields=policy.bind_fields,
            description=policy.description,
            entities_file=entities_file,
        )
    if not grains:
        return None
    return grains


def _resolve_default_grain(
    grains: dict[str, GrainMvrPolicy],
    declared: str | None,
) -> str:
    if declared:
        default = declared.strip()
        if default not in grains:
            raise ValueError(
                f"network.json mvr.default_grain {default!r} is not declared in mvr.grains",
            )
        return default
    grain_names = sorted(grains.keys())
    if len(grains) == 1:
        return grain_names[0]
    raise ValueError(
        "network.json mvr.default_grain is required when multiple grains are declared",
    )


def load_mvr_config(*, paths: NetworkPaths | None = None) -> NetworkMvrConfig:
    """Load multi-grain MVR configuration from ``network.json``."""
    if paths is None:
        root = resolve_network_root()
        paths = NetworkPaths.from_root(root)

    network_json = paths.root / "network.json"
    if not network_json.is_file():
        return _crm_default_config()

    try:
        data = json.loads(network_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _crm_default_config()

    if not isinstance(data, dict):
        return _crm_default_config()

    mvr_raw = data.get("mvr")
    if not isinstance(mvr_raw, dict):
        return _crm_default_config()

    grains = _parse_grains_block(mvr_raw)
    if grains is not None:
        default_raw = mvr_raw.get("default_grain")
        declared = (
            str(default_raw).strip() if isinstance(default_raw, str) else None
        )
        default_grain = _resolve_default_grain(grains, declared)
        return NetworkMvrConfig(default_grain=default_grain, grains=grains)

    parsed = _parse_mvr_block(mvr_raw)
    if parsed is not None:
        grain = GrainMvrPolicy(
            bind_fields=parsed.bind_fields,
            description=parsed.description,
            entities_file="entities/person.json",
        )
        return NetworkMvrConfig(default_grain="person", grains={"person": grain})

    return _crm_default_config()


def default_mvr_grain(*, paths: NetworkPaths | None = None) -> str:
    """Return the default query grain for the active network."""
    return load_mvr_config(paths=paths).default_grain


def list_mvr_grains(*, paths: NetworkPaths | None = None) -> list[str]:
    """Return declared MVR grain names (sorted)."""
    return sorted(load_mvr_config(paths=paths).grains.keys())


def load_mvr(*, paths: NetworkPaths | None = None, grain: str | None = None) -> MvrPolicy:
    """Load MVR policy for a grain; default grain when ``grain`` is omitted."""
    config = load_mvr_config(paths=paths)
    grain_name = grain or config.default_grain
    if grain_name not in config.grains:
        known = ", ".join(sorted(config.grains.keys()))
        raise ValueError(
            f"Unknown MVR grain {grain_name!r}; declared grains: {known}",
        )
    return config.grains[grain_name].to_mvr_policy()


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

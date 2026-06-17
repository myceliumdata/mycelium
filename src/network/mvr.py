"""Minimum viable record (MVR) policy from ``network.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from network.paths import NetworkPaths, resolve_network_root

_DEFAULT_DESCRIPTION = (
    "Minimum bind fields required before entity research (declared per grain in network.json)."
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


def _manifest_path(paths: NetworkPaths) -> Path:
    return paths.root / "network.json"


def _load_manifest_dict(paths: NetworkPaths) -> dict[str, Any]:
    manifest_path = _manifest_path(paths)
    if not manifest_path.is_file():
        raise ValueError(
            f"{manifest_path}: network manifest required "
            "(add network.json with mvr.grains and mvr.default_grain)",
        )
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid network.json at {manifest_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{manifest_path}: network.json must be a JSON object")
    return data


def _parse_grain_policy(raw: Any, *, grain_name: str, manifest_path: Path) -> MvrPolicy:
    if not isinstance(raw, dict):
        raise ValueError(
            f"{manifest_path}: mvr.grains.{grain_name} must be an object",
        )
    bind_fields = raw.get("bind_fields")
    if not isinstance(bind_fields, list) or not bind_fields:
        raise ValueError(
            f"{manifest_path}: mvr.grains.{grain_name} requires non-empty bind_fields",
        )
    fields = [str(item).strip() for item in bind_fields if str(item).strip()]
    if not fields:
        raise ValueError(
            f"{manifest_path}: mvr.grains.{grain_name} requires non-empty bind_fields",
        )
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        description = _DEFAULT_DESCRIPTION
    return MvrPolicy(bind_fields=fields, description=description.strip())


def _parse_grains_block(
    mvr_raw: dict[str, Any],
    *,
    manifest_path: Path,
) -> dict[str, GrainMvrPolicy]:
    if "bind_fields" in mvr_raw and "grains" not in mvr_raw:
        raise ValueError(
            f"{manifest_path}: flat mvr.bind_fields is not supported; "
            "declare mvr.grains.<name>.bind_fields instead",
        )
    grains_raw = mvr_raw.get("grains")
    if not isinstance(grains_raw, dict) or not grains_raw:
        raise ValueError(
            f"{manifest_path}: missing required mvr.grains object "
            '(e.g. "grains": {"person": {"bind_fields": ["name", "employer"], ...}})',
        )
    grains: dict[str, GrainMvrPolicy] = {}
    for grain_name, grain_raw in grains_raw.items():
        name = str(grain_name).strip()
        if not name:
            continue
        policy = _parse_grain_policy(grain_raw, grain_name=name, manifest_path=manifest_path)
        entities_file_raw = grain_raw.get("entities_file") if isinstance(grain_raw, dict) else None
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
        raise ValueError(
            f"{manifest_path}: mvr.grains must declare at least one grain",
        )
    return grains


def load_mvr_config(*, paths: NetworkPaths | None = None) -> NetworkMvrConfig:
    """Load multi-grain MVR configuration from ``network.json``."""
    if paths is None:
        root = resolve_network_root()
        paths = NetworkPaths.from_root(root)

    manifest_path = _manifest_path(paths)
    data = _load_manifest_dict(paths)
    mvr_raw = data.get("mvr")
    if not isinstance(mvr_raw, dict):
        raise ValueError(
            f"{manifest_path}: missing required mvr object "
            '(declare "mvr": {"default_grain": "...", "grains": {...}})',
        )

    grains = _parse_grains_block(mvr_raw, manifest_path=manifest_path)
    default_raw = mvr_raw.get("default_grain")
    if not isinstance(default_raw, str) or not default_raw.strip():
        raise ValueError(
            f"{manifest_path}: missing required mvr.default_grain",
        )
    default_grain = default_raw.strip()
    if default_grain not in grains:
        raise ValueError(
            f"{manifest_path}: mvr.default_grain {default_grain!r} "
            "is not declared in mvr.grains",
        )
    return NetworkMvrConfig(default_grain=default_grain, grains=grains)


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


def mvr_bind_field_names(mvr: MvrPolicy | None = None) -> list[str]:
    """Lower-case active MVR bind field names."""
    policy = mvr if mvr is not None else load_mvr()
    return [field.strip().lower() for field in policy.bind_fields if field.strip()]


def mvr_bind_field_set(mvr: MvrPolicy | None = None) -> frozenset[str]:
    """Frozen set of active MVR bind field names."""
    return frozenset(mvr_bind_field_names(mvr))

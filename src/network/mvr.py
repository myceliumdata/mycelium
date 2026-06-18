"""Minimum viable record (MVR) policy from ``network.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from network.paths import NetworkPaths, resolve_network_root

_DEFAULT_DESCRIPTION = (
    "Minimum bind fields required before entity research "
    "(declared per record_type in network.json)."
)

NewRecordsPolicy = Literal["bootstrap_only", "query_allowed"]

_LEGACY_MVR_KEYS = frozenset({"grains", "default_grain"})
_LEGACY_RECORD_TYPE_KEYS = frozenset({"identity_mode"})


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
class RecordTypePolicy:
    """Per-record-type MVR policy plus entity store path relative to network root."""

    bind_fields: list[str]
    description: str
    entities_file: str
    new_records: NewRecordsPolicy

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
            "new_records": self.new_records,
        }


@dataclass(frozen=True)
class NetworkMvrConfig:
    """Multi-record-type MVR configuration from ``network.json``."""

    default_record_type: str
    record_types: dict[str, RecordTypePolicy]

    def summary(self) -> dict[str, Any]:
        return {
            "default_record_type": self.default_record_type,
            "record_types": {
                name: record_type.summary()
                for name, record_type in self.record_types.items()
            },
        }


def _manifest_path(paths: NetworkPaths) -> Path:
    return paths.root / "network.json"


def _load_manifest_dict(paths: NetworkPaths) -> dict[str, Any]:
    manifest_path = _manifest_path(paths)
    if not manifest_path.is_file():
        raise ValueError(
            f"{manifest_path}: network manifest required "
            "(add network.json with mvr.record_types and mvr.default_record_type)",
        )
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid network.json at {manifest_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{manifest_path}: network.json must be a JSON object")
    return data


def _reject_legacy_mvr_keys(mvr_raw: dict[str, Any], *, manifest_path: Path) -> None:
    for key in _LEGACY_MVR_KEYS:
        if key in mvr_raw:
            raise ValueError(
                f"{manifest_path}: legacy mvr.{key} is not supported; "
                "use mvr.record_types and mvr.default_record_type",
            )


def _parse_new_records(raw: Any, *, record_type_name: str, manifest_path: Path) -> NewRecordsPolicy:
    if raw is None:
        raise ValueError(
            f"{manifest_path}: mvr.record_types.{record_type_name} requires new_records "
            '("bootstrap_only" or "query_allowed")',
        )
    text = str(raw).strip().lower()
    if text == "bootstrap_only":
        return "bootstrap_only"
    if text == "query_allowed":
        return "query_allowed"
    raise ValueError(
        f"{manifest_path}: mvr.record_types.{record_type_name}.new_records "
        f"must be bootstrap_only or query_allowed, got {raw!r}",
    )


def _parse_record_type_policy(
    raw: Any,
    *,
    record_type_name: str,
    manifest_path: Path,
) -> MvrPolicy:
    if not isinstance(raw, dict):
        raise ValueError(
            f"{manifest_path}: mvr.record_types.{record_type_name} must be an object",
        )
    for key in _LEGACY_RECORD_TYPE_KEYS:
        if key in raw:
            raise ValueError(
                f"{manifest_path}: legacy identity_mode on "
                f"mvr.record_types.{record_type_name} is not supported; "
                "use new_records",
            )
    bind_fields = raw.get("bind_fields")
    if not isinstance(bind_fields, list) or not bind_fields:
        raise ValueError(
            f"{manifest_path}: mvr.record_types.{record_type_name} "
            "requires non-empty bind_fields",
        )
    fields = [str(item).strip() for item in bind_fields if str(item).strip()]
    if not fields:
        raise ValueError(
            f"{manifest_path}: mvr.record_types.{record_type_name} "
            "requires non-empty bind_fields",
        )
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        description = _DEFAULT_DESCRIPTION
    return MvrPolicy(bind_fields=fields, description=description.strip())


def _parse_record_types_block(
    mvr_raw: dict[str, Any],
    *,
    manifest_path: Path,
) -> dict[str, RecordTypePolicy]:
    _reject_legacy_mvr_keys(mvr_raw, manifest_path=manifest_path)
    if "bind_fields" in mvr_raw and "record_types" not in mvr_raw:
        raise ValueError(
            f"{manifest_path}: flat mvr.bind_fields is not supported; "
            "declare mvr.record_types.<name>.bind_fields instead",
        )
    record_types_raw = mvr_raw.get("record_types")
    if not isinstance(record_types_raw, dict) or not record_types_raw:
        raise ValueError(
            f"{manifest_path}: missing required mvr.record_types object "
            '(e.g. "record_types": {"person": {"bind_fields": ["name", "employer"], ...}})',
        )
    record_types: dict[str, RecordTypePolicy] = {}
    for record_type_name, record_type_raw in record_types_raw.items():
        name = str(record_type_name).strip()
        if not name:
            continue
        policy = _parse_record_type_policy(
            record_type_raw,
            record_type_name=name,
            manifest_path=manifest_path,
        )
        if not isinstance(record_type_raw, dict):
            raise ValueError(
                f"{manifest_path}: mvr.record_types.{name} must be an object",
            )
        entities_file_raw = record_type_raw.get("entities_file")
        if isinstance(entities_file_raw, str) and entities_file_raw.strip():
            entities_file = entities_file_raw.strip()
        else:
            entities_file = f"entities/{name}.json"
        new_records = _parse_new_records(
            record_type_raw.get("new_records"),
            record_type_name=name,
            manifest_path=manifest_path,
        )
        record_types[name] = RecordTypePolicy(
            bind_fields=policy.bind_fields,
            description=policy.description,
            entities_file=entities_file,
            new_records=new_records,
        )
    if not record_types:
        raise ValueError(
            f"{manifest_path}: mvr.record_types must declare at least one record type",
        )
    return record_types


def load_mvr_config(*, paths: NetworkPaths | None = None) -> NetworkMvrConfig:
    """Load multi-record-type MVR configuration from ``network.json``."""
    if paths is None:
        root = resolve_network_root()
        paths = NetworkPaths.from_root(root)

    manifest_path = _manifest_path(paths)
    data = _load_manifest_dict(paths)
    mvr_raw = data.get("mvr")
    if not isinstance(mvr_raw, dict):
        raise ValueError(
            f"{manifest_path}: missing required mvr object "
            '(declare "mvr": {"default_record_type": "...", "record_types": {...}})',
        )

    record_types = _parse_record_types_block(mvr_raw, manifest_path=manifest_path)
    default_raw = mvr_raw.get("default_record_type")
    if not isinstance(default_raw, str) or not default_raw.strip():
        raise ValueError(
            f"{manifest_path}: missing required mvr.default_record_type",
        )
    default_record_type = default_raw.strip()
    if default_record_type not in record_types:
        raise ValueError(
            f"{manifest_path}: mvr.default_record_type {default_record_type!r} "
            "is not declared in mvr.record_types",
        )
    return NetworkMvrConfig(
        default_record_type=default_record_type,
        record_types=record_types,
    )


def default_record_type(*, paths: NetworkPaths | None = None) -> str:
    """Return the default query record type for the active network."""
    return load_mvr_config(paths=paths).default_record_type


def list_record_types(*, paths: NetworkPaths | None = None) -> list[str]:
    """Return declared MVR record type names (sorted)."""
    return sorted(load_mvr_config(paths=paths).record_types.keys())


def load_mvr(
    *,
    paths: NetworkPaths | None = None,
    record_type: str | None = None,
) -> MvrPolicy:
    """Load MVR policy for a record type; default when ``record_type`` is omitted."""
    config = load_mvr_config(paths=paths)
    record_type_name = record_type or config.default_record_type
    if record_type_name not in config.record_types:
        known = ", ".join(sorted(config.record_types.keys()))
        raise ValueError(
            f"Unknown MVR record type {record_type_name!r}; declared: {known}",
        )
    return config.record_types[record_type_name].to_mvr_policy()


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


def is_bootstrap_only_record_type(
    record_type: str | None = None,
    *,
    paths: NetworkPaths | None = None,
) -> bool:
    """True when the record type forbids query-time entity creation."""
    config = load_mvr_config(paths=paths)
    record_type_name = record_type or config.default_record_type
    policy = config.record_types.get(record_type_name)
    if policy is None:
        return False
    return policy.new_records == "bootstrap_only"


@dataclass(frozen=True)
class RecordTypeInferenceResult:
    """Result of inferring MVR record type from step-1 lookup key shape."""

    kind: str
    record_type: str | None = None
    required_fields: tuple[str, ...] = ()
    message: str | None = None


def _all_declared_bind_fields(config: NetworkMvrConfig | None = None) -> set[str]:
    cfg = config or load_mvr_config()
    fields: set[str] = set()
    for record_type_policy in cfg.record_types.values():
        fields.update(
            field.strip().lower()
            for field in record_type_policy.bind_fields
            if field.strip()
        )
    return fields


def infer_record_type_from_lookup(
    lookup: dict[str, str],
    *,
    config: NetworkMvrConfig | None = None,
) -> RecordTypeInferenceResult:
    """Infer exactly one MVR record type from lookup keys (disjoint bind field names).

    A record type matches when normalized lookup keys equal that type's bind_fields
    set exactly. Partial subsets yield lookup_incomplete; unknown keys yield not_found.
    """
    cfg = config or load_mvr_config()
    norm = normalized_lookup_values(lookup)
    if not norm:
        return RecordTypeInferenceResult(kind="not_found")

    provided = set(norm.keys())
    all_fields = _all_declared_bind_fields(cfg)
    if not provided.issubset(all_fields):
        return RecordTypeInferenceResult(kind="not_found")

    exact_matches: list[str] = []
    for record_type_name in sorted(cfg.record_types.keys()):
        required = {
            field.strip().lower()
            for field in cfg.record_types[record_type_name].bind_fields
            if field.strip()
        }
        if required == provided:
            exact_matches.append(record_type_name)

    if len(exact_matches) == 1:
        return RecordTypeInferenceResult(
            kind="resolved_record_type",
            record_type=exact_matches[0],
        )
    if len(exact_matches) > 1:
        return RecordTypeInferenceResult(
            kind="ambiguous",
            message="ambiguous lookup keys for multiple record types",
        )

    incomplete: list[tuple[str, list[str]]] = []
    for record_type_name in sorted(cfg.record_types.keys()):
        required = {
            field.strip().lower()
            for field in cfg.record_types[record_type_name].bind_fields
            if field.strip()
        }
        if provided and provided < required:
            missing = sorted(required - provided)
            incomplete.append((record_type_name, missing))

    if incomplete:
        record_type_name, missing = min(incomplete, key=lambda item: len(item[1]))
        return RecordTypeInferenceResult(
            kind="lookup_incomplete",
            record_type=record_type_name,
            required_fields=tuple(missing),
        )

    return RecordTypeInferenceResult(kind="not_found")

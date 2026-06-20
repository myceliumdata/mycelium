"""Per-network MCP health_check step-1 lookup from ``network.json``."""

from __future__ import annotations

import json
from typing import Any

from network.mvr import infer_record_type_from_lookup, load_mvr_config
from network.paths import NetworkPaths, resolve_network_root


def _load_manifest_dict(paths: NetworkPaths) -> dict[str, Any] | None:
    manifest_path = paths.root / "network.json"
    if not manifest_path.is_file():
        return None

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def resolve_health_ping_lookup(*, paths: NetworkPaths | None = None) -> dict[str, str] | None:
    """
    Return a step-1 lookup dict for MCP ``health_check`` ping, or ``None`` when unset.

    Operators declare ``health_ping.lookup`` in ``network.json`` with bind-field keys that
    match exactly one record type (same contract as client lookups). Networks without a
    configured ping (for example empty-seed CRM before growth) skip the query sub-check.
    """
    if paths is None:
        root = resolve_network_root()
        paths = NetworkPaths.from_root(root)

    manifest = _load_manifest_dict(paths)
    if manifest is None:
        return None

    health_ping = manifest.get("health_ping")
    if not isinstance(health_ping, dict):
        return None

    lookup_raw = health_ping.get("lookup")
    if not isinstance(lookup_raw, dict) or not lookup_raw:
        return None

    lookup: dict[str, str] = {}
    for key, value in lookup_raw.items():
        if not isinstance(key, str) or not key.strip():
            continue
        if value is None:
            continue
        text = str(value).strip()
        if text:
            lookup[key.strip()] = text

    if not lookup:
        return None

    config = load_mvr_config(paths=paths)
    inference = infer_record_type_from_lookup(lookup, config=config)
    if inference.record_type is None:
        return None

    return lookup
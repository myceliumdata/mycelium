"""Per-network intent map: requested attribute label → canonical intent slug."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from network.paths import NetworkPaths

_INTENT_MAP_VERSION = "1.0"


def intent_map_path(paths: NetworkPaths) -> Path:
    return paths.root / "intent_map.json"


def _normalize_label(label: str) -> str:
    return label.strip().lower()


def lookup_intent_slug(label: str, mappings: dict[str, str]) -> str | None:
    key = _normalize_label(label)
    slug = mappings.get(key)
    if slug is None:
        return None
    text = str(slug).strip().lower()
    return text or None


def load_intent_map(paths: NetworkPaths) -> dict[str, str]:
    path = intent_map_path(paths)
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    mappings = raw.get("mappings")
    if not isinstance(mappings, dict):
        return {}
    result: dict[str, str] = {}
    for label, slug in mappings.items():
        key = _normalize_label(str(label))
        value = str(slug).strip().lower()
        if key and value:
            result[key] = value
    return result


def save_intent_mapping(paths: NetworkPaths, label: str, intent_slug: str) -> None:
    key = _normalize_label(label)
    slug = intent_slug.strip().lower()
    if not key or not slug:
        return

    path = intent_map_path(paths)
    existing = load_intent_map(paths)
    if existing.get(key) == slug:
        return

    existing[key] = slug
    payload: dict[str, Any] = {
        "version": _INTENT_MAP_VERSION,
        "mappings": dict(sorted(existing.items())),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2) + "\n"
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def labels_for_intent_slug(intent_slug: str, intent_map: dict[str, str]) -> set[str]:
    slug = intent_slug.strip().lower()
    keys = {slug}
    keys.update(label for label, mapped in intent_map.items() if mapped == slug)
    return keys

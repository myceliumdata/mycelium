"""Computed-field version bodies for warehouse-backed specialist writes."""

from __future__ import annotations

from typing import Any

from agents.specialists.fields import append_version


def build_computed_version_body(
    *,
    value: str,
    actor: dict[str, str],
    sources: list[dict[str, Any]],
    computation: dict[str, str],
    parameters: dict[str, str],
    at: str,
    status: str = "found",
) -> dict[str, Any]:
    """Build a version dict for a computed specialist field."""
    return {
        "at": at,
        "status": status,
        "value": str(value).strip(),
        "actor": dict(actor),
        "sources": list(sources),
        "computation": dict(computation),
        "parameters": dict(parameters),
    }


def append_computed_version(
    entry: dict[str, Any] | None,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Append a computed version using the shared versioned-field store."""
    return append_version(entry, body)

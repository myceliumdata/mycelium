"""Shared environment variable helpers for network runtime modules."""

from __future__ import annotations

import os


def env_int(name: str, default: int) -> int:
    """Parse a positive integer from ``name``; return ``default`` when unset or invalid."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

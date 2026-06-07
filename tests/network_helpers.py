"""Shared helpers for network path isolation in tests."""

from __future__ import annotations

import pytest

NETWORK_PATH_ENV_KEYS = (
    "MYCELIUM_NETWORK_ROOT",
    "MYCELIUM_SEED_PATH",
    "MYCELIUM_AGENT_REGISTRY_PATH",
    "MYCELIUM_CATEGORIES_PATH",
    "MYCELIUM_AGENT_DATA_DIR",
    "MYCELIUM_SPECIALISTS_DIR",
    "MYCELIUM_CHECKPOINT_PATH",
    "MYCELIUM_DB_PATH",
)


def clear_network_path_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop path vars set by apply_network_paths (not tracked by monkeypatch undo)."""
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    for key in NETWORK_PATH_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

"""Smoke tests for MCP runtime disk refresh (long-lived server parity with CLI)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from agents.registry import get_agent_registry, reset_agent_registry
from agents.runtime import evict_cached_specialist_modules, refresh_runtime_from_disk


@pytest.fixture
def runtime_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    reg_path = tmp_path / "agent_registry.json"
    monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(reg_path))
    reset_agent_registry()
    yield reg_path
    reset_agent_registry()
    evict_cached_specialist_modules()


@pytest.mark.smoke
def test_refresh_runtime_loads_registry_written_after_singleton_init(
    runtime_env: Path,
) -> None:
    """Disk registry updated after first load is visible after refresh_runtime_from_disk."""
    _ = get_agent_registry()
    assert get_agent_registry().list_agents() == []

    runtime_env.write_text(
        json.dumps(
            {
                "version": "1.0",
                "last_updated": "2026-06-05T12:00:00+00:00",
                "agents": {
                    "contact_specialist": {
                        "name": "contact_specialist",
                        "category": "contact",
                        "description": "Contact specialist",
                        "module_path": "agents.specialists.contact_specialist",
                        "entrypoint": "contact_specialist",
                        "storage_path": "data/agents/contact/storage.json",
                        "strategy_path": "data/agents/contact/storage_strategy.json",
                        "is_generated": True,
                        "created_at": "2026-06-05T12:00:00+00:00",
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    refresh_runtime_from_disk(reload_dotenv=False)

    reg = get_agent_registry()
    assert reg.has_agent("contact_specialist")
    assert len(reg.list_agents()) == 1


@pytest.mark.smoke
def test_evict_cached_specialist_modules_removes_dyn_and_generated() -> None:
    """Specialist module eviction clears dyn_* and generated *_specialist entries."""
    import types

    import agents.specialists.base as real_base

    dyn_name = "dyn_specialist_demo_specialist"
    gen_name = "agents.specialists.demo_specialist"
    sys.modules[dyn_name] = types.ModuleType(dyn_name)
    sys.modules[gen_name] = types.ModuleType(gen_name)

    removed = evict_cached_specialist_modules()

    assert dyn_name in removed
    assert gen_name in removed
    assert dyn_name not in sys.modules
    assert gen_name not in sys.modules
    assert sys.modules.get("agents.specialists.base") is real_base

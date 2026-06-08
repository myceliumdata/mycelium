"""Agent Registry (<network_root>/agent_registry.json + in-memory).

See approved plan 'Agent Registry' design (docs/plans/agent-factory-phase2.md).
Generated specialists are loaded from MYCELIUM_SPECIALISTS_DIR (factory tests).
Atomic save per Phase 1 classification pattern. No privileged core agent.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

# Embedded fallback when registry file is missing (empty; specialists added via factory).
_SEED_REGISTRY: dict[str, Any] = {
    "version": "1.0",
    "last_updated": "2026-06-03T00:00:00+00:00",
    "agents": {},
}


class RegisteredAgent(BaseModel):
    """A registered generated specialist."""

    name: str
    category: str
    description: str
    module_path: str
    entrypoint: str
    storage_path: str | None = None
    strategy_path: str | None = None
    is_generated: bool = False
    created_at: str | None = None


class AgentRegistryData(BaseModel):
    """The serializable shape of the agent registry (written to JSON)."""

    version: str = "1.0"
    last_updated: datetime
    agents: dict[str, RegisteredAgent]


def _default_registry_path() -> Path:
    from network.paths import runtime_path

    return runtime_path("MYCELIUM_AGENT_REGISTRY_PATH")


class AgentRegistry:
    """In-memory agent registry with persistent JSON cache."""

    def __init__(self, registry_path: Path | None = None) -> None:
        self.registry_path = registry_path or _default_registry_path()
        self._data: AgentRegistryData | None = None
        self._load()

    def _load(self) -> None:
        if self.registry_path.exists():
            raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
            self._data = AgentRegistryData.model_validate(raw)
        else:
            self._data = self._create_seed()
            self._save()

    def _save(self) -> None:
        """Atomic write via temp file + replace (matches classification/engine.py)."""
        if self._data is None:
            return
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._data.model_dump_json(indent=2)
        fd, tmp_path = tempfile.mkstemp(
            dir=self.registry_path.parent,
            suffix=".json.tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_path, self.registry_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _create_seed(self) -> AgentRegistryData:
        return AgentRegistryData.model_validate(_SEED_REGISTRY)

    def reload(self) -> None:
        self._load()

    def has_agent(self, name: str) -> bool:
        if self._data is None:
            self._load()
        return name in self._data.agents

    def _load_agent_fn(
        self,
        entry: RegisteredAgent,
    ) -> Callable[[Any], dict[str, Any]] | None:
        from network.paths import runtime_path

        specialists_dir = runtime_path("MYCELIUM_SPECIALISTS_DIR")
        py_file = specialists_dir / f"{entry.name}.py"
        if py_file.exists():
            spec = importlib.util.spec_from_file_location(
                f"dyn_specialist_{entry.name}",
                str(py_file),
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                fn = getattr(mod, entry.entrypoint, None)
                if callable(fn):
                    return fn
                return None

        try:
            mod = importlib.import_module(entry.module_path)
            return getattr(mod, entry.entrypoint, None)
        except Exception:
            return None

    def get_agent_fn(self, name: str) -> Callable[[Any], dict[str, Any]] | None:
        if self._data is None:
            self._load()
        entry = self._data.agents.get(name)
        if entry is None:
            return None
        return self._load_agent_fn(entry)

    def register_agent(
        self,
        entry: dict[str, Any] | RegisteredAgent,
        *,
        save: bool = True,
    ) -> None:
        if self._data is None:
            self._load()
        agent = (
            entry
            if isinstance(entry, RegisteredAgent)
            else RegisteredAgent.model_validate(entry)
        )
        self._data.agents[agent.name] = agent
        self._data.last_updated = datetime.now(timezone.utc)
        if save:
            self._save()

    def list_agents(self) -> list[dict[str, Any]]:
        if self._data is None:
            self._load()
        return [agent.model_dump() for agent in self._data.agents.values()]


_agent_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    """Process-wide cached AgentRegistry (lazy; respects MYCELIUM_AGENT_REGISTRY_PATH)."""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


def reset_agent_registry() -> None:
    """Clear the singleton (for tests + admin reload scenarios)."""
    global _agent_registry
    _agent_registry = None

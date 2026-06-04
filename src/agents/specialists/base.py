"""Base for generated specialists. Provides storage helper + future upgrade hooks (see approved plan)."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SpecialistStorage:
    """Per-specialist flat-JSON storage with explicit strategy metadata for future self-evolution.

    Each generated specialist gets its own directory under data/agents/<category>/.
    The specialist code (committed) can later contain intelligence that decides when
    to call .migrate_to(...) based on its own data volume, query patterns, etc.
    Implemented per approved plan Step 3.
    """

    def __init__(self, category: str, base_dir: Path | None = None) -> None:
        self.category = category
        self.base_dir = (
            base_dir or Path(os.getenv("MYCELIUM_AGENT_DATA_DIR", "data/agents"))
        ) / self._slug(category)
        self.storage_file = self.base_dir / "storage.json"
        self.strategy_file = self.base_dir / "storage_strategy.json"
        self._ensure_initialized()

    def _slug(self, c: str) -> str:
        return c.strip().lower().replace(" ", "_").replace("-", "_")

    def _ensure_initialized(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if not self.strategy_file.exists():
            strategy = {
                "strategy": "flat_json_v1",
                "version": "1.0",
                "last_migrated": None,
                "upgrade_path": {
                    "flat_json_v1": {
                        "description": (
                            "Simple per-agent JSON file. Suitable for small-to-medium "
                            "specialist datasets."
                        ),
                        "next_candidates": ["minisql_v1"],
                    },
                },
            }
            self._atomic_write(self.strategy_file, strategy)
        if not self.storage_file.exists():
            # records keyed by person_id (uuid from seed loader), e.g.:
            # {"<person-id>": {"email": "a@b.com", "phone": {"status": "pending", ...},
            #                  "linkedin": {"status": "na"}}}
            initial = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "records": {},
                "meta": {"created_by": "agent-factory"},
            }
            self._atomic_write(self.storage_file, initial)

    def _atomic_write(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(payload, indent=2)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(data)
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def load(self) -> dict[str, Any]:
        if not self.storage_file.exists():
            self._ensure_initialized()
        return json.loads(self.storage_file.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        payload = dict(data)
        payload["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._atomic_write(self.storage_file, payload)

    def get_strategy(self) -> dict[str, Any]:
        if not self.strategy_file.exists():
            self._ensure_initialized()
        return json.loads(self.strategy_file.read_text(encoding="utf-8"))

    def current_strategy(self) -> str:
        return self.get_strategy().get("strategy", "flat_json_v1")

    def migrate_to(self, target: str) -> None:
        """Future hook for agent self-managed storage evolution.

        A specialist agent (the generated .py) can decide (based on its own data volume,
        access patterns, config, or even LLM advice) to call this. Base implementation
        can later contain actual migration (copy data, swap files, update strategy json).
        For Phase 2 this is a deliberate no-op / documented extension point.
        """
        current = self.current_strategy()
        if current == target:
            return
        raise NotImplementedError(
            f"Storage migration from {current} to {target} not implemented in this "
            f"version of the {self.category} specialist. "
            "Edit the specialist or extend base.py to add migration logic."
        )

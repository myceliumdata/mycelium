"""Per-grain entity store persistence (JSON or minisql_v1)."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agents.entity_registry import EntitiesDocument


class EntityStore:
    """Load/save ``EntitiesDocument`` with strategy metadata and migration hooks."""

    def __init__(
        self,
        grain: str,
        json_path: Path,
        strategy_path: Path,
        sqlite_path: Path,
    ) -> None:
        self.grain = grain
        self.json_path = json_path
        self.strategy_path = strategy_path
        self.sqlite_path = sqlite_path
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.strategy_path.is_file():
            strategy = {
                "strategy": "entities_document_v1",
                "version": "1.0",
                "grain": self.grain,
                "notes": (
                    "Per-grain entity registry document with bind_index. "
                    "Migrates to minisql_v1 at optimize_storage threshold."
                ),
                "last_migrated": None,
                "upgrade_path": {
                    "entities_document_v1": {
                        "description": "Single JSON document per grain with entities + bind_index.",
                        "next_candidates": ["minisql_v1"],
                    },
                },
            }
            self._atomic_write_json(self.strategy_path, strategy)

        if self.current_strategy() == "minisql_v1":
            if not self.sqlite_path.is_file():
                from storage.minisql_v1 import _ensure_entity_sqlite

                _ensure_entity_sqlite(self.sqlite_path)

    def _atomic_write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(payload, indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(data)
            os.replace(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def get_strategy(self) -> dict[str, Any]:
        if not self.strategy_path.is_file():
            self._ensure_initialized()
        return json.loads(self.strategy_path.read_text(encoding="utf-8"))

    def current_strategy(self) -> str:
        return self.get_strategy().get("strategy", "entities_document_v1")

    def entity_count(self, document: EntitiesDocument) -> int:
        return len(document.entities)

    def load(self) -> EntitiesDocument:
        from agents.entity_registry import EntitiesDocument, _reject_legacy_entity_rows

        if self.current_strategy() == "minisql_v1":
            from storage.minisql_v1 import load_entities_document

            raw = load_entities_document(self.sqlite_path)
            _reject_legacy_entity_rows(raw, self.json_path)
            return EntitiesDocument.model_validate(raw)

        if not self.json_path.is_file():
            return EntitiesDocument()

        raw = json.loads(self.json_path.read_text(encoding="utf-8"))
        _reject_legacy_entity_rows(raw, self.json_path)
        return EntitiesDocument.model_validate(raw)

    def save(self, document: EntitiesDocument) -> None:
        payload = document.model_dump()
        payload["last_updated"] = datetime.now(timezone.utc).isoformat()
        if self.current_strategy() == "minisql_v1":
            from storage.minisql_v1 import save_entities_document

            save_entities_document(self.sqlite_path, payload)
            return
        self._atomic_write_json(self.json_path, payload)

    def migrate_to(self, target: str) -> None:
        current = self.current_strategy()
        if current == target:
            return
        if target == "minisql_v1" and current == "entities_document_v1":
            from storage.minisql_v1 import migrate_entities_document_v1_json

            migrate_entities_document_v1_json(
                self.json_path,
                self.sqlite_path,
                grain=self.grain,
            )
            backup_path = self.json_path.parent / f"{self.json_path.stem}.json.pre-minisql-v1"
            if self.json_path.is_file():
                if backup_path.exists():
                    backup_path.unlink()
                self.json_path.rename(backup_path)
            strategy = self.get_strategy()
            strategy["strategy"] = "minisql_v1"
            strategy["last_migrated"] = datetime.now(timezone.utc).isoformat()
            self._atomic_write_json(self.strategy_path, strategy)
            return
        raise NotImplementedError(
            f"Entity storage migration from {current} to {target} not implemented "
            f"for grain {self.grain!r}.",
        )

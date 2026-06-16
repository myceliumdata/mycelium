"""Base for generated specialists. Provides storage helper + future upgrade hooks.

Framework ``*_specialist.py`` modules under ``src/agents/specialists/`` are committed
(import_module fallback + CI). Regenerate from ``specialist_agent.py.j2`` when the
template changes.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def category_slug(category: str) -> str:
    """Normalize a category name to a filesystem-safe slug."""
    return category.strip().lower().replace(" ", "_").replace("-", "_")


def registry_storage_paths(category: str) -> tuple[str, str]:
    """Return storage paths for registry metadata (network-relative when possible).

    Does not create directories — safe for ontology/bootstrap paths only.
    """
    slug = category_slug(category)
    from network.paths import runtime_path

    agents_base = runtime_path("MYCELIUM_AGENT_DATA_DIR")
    storage_file = agents_base / slug / "storage.json"
    strategy_file = agents_base / slug / "storage_strategy.json"

    network_root = os.getenv("MYCELIUM_NETWORK_ROOT", "").strip()
    if network_root:
        root = Path(network_root).expanduser().resolve()
        agents_resolved = agents_base.expanduser().resolve()
        if agents_resolved.is_relative_to(root):
            return (
                str(storage_file.resolve().relative_to(root)),
                str(strategy_file.resolve().relative_to(root)),
            )
    return (str(storage_file), str(strategy_file))


class SpecialistStorage:
    """Per-specialist flat-JSON storage with explicit strategy metadata for future self-evolution.

    Each generated specialist gets its own directory under <network_root>/agents/<category>/.
    The specialist code (committed) can later contain intelligence that decides when
    to call .migrate_to(...) based on its own data volume, query patterns, etc.
    Implemented per approved plan Step 3.
    """

    def __init__(self, category: str, base_dir: Path | None = None) -> None:
        self.category = category
        if base_dir is None:
            from network.paths import runtime_path

            base_dir = runtime_path("MYCELIUM_AGENT_DATA_DIR")
        self.base_dir = base_dir / self._slug(category)
        self.storage_file = self.base_dir / "storage.json"
        self.sqlite_file = self.base_dir / "storage.sqlite"
        self.strategy_file = self.base_dir / "storage_strategy.json"
        self._ensure_initialized()

    def _slug(self, c: str) -> str:
        return category_slug(c)

    def _ensure_initialized(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if not self.strategy_file.exists():
            strategy = {
                "strategy": "versioned_provenance_v1",
                "version": "2.1",
                "bind_field_ownership": "taxonomy",
                "stored_fields": "extended_attributes_and_mvr_bind_fields",
                "notes": (
                    "Extended attributes and MVR bind fields (name, employer, etc.) use "
                    "versioned_provenance_v1 (versions[] per field) in taxonomy-owned "
                    "specialist storage. Entity row caches current values. "
                    "Flat v1 field blobs are invalid — refresh the network to reset."
                ),
                "last_migrated": None,
                "upgrade_path": {
                    "versioned_provenance_v1": {
                        "description": (
                            "Append-only versions[] per extended attribute with actor and sources."
                        ),
                        "next_candidates": ["minisql_v1"],
                    },
                },
            }
            self._atomic_write(self.strategy_file, strategy)

        strategy_name = self.current_strategy()
        if strategy_name == "minisql_v1":
            from storage.minisql_v1 import ensure_empty_sqlite

            if not self.sqlite_file.exists():
                ensure_empty_sqlite(self.sqlite_file)
            return

        if not self.storage_file.exists():
            # records keyed by id (uuid from seed loader), e.g.:
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
        if self.current_strategy() == "minisql_v1":
            from storage.minisql_v1 import load_payload

            return load_payload(self.sqlite_file)
        if not self.storage_file.exists():
            self._ensure_initialized()
        return json.loads(self.storage_file.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        if self.current_strategy() == "minisql_v1":
            from storage.minisql_v1 import save_payload

            save_payload(self.sqlite_file, data)
            return
        payload = dict(data)
        payload["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._atomic_write(self.storage_file, payload)

    def load_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Return one entity's field map, or ``None`` when the entity is absent."""
        if self.current_strategy() == "minisql_v1":
            from storage.minisql_v1 import load_entity_record

            return load_entity_record(self.sqlite_file, entity_id)
        records = self.load().get("records", {})
        if not isinstance(records, dict) or entity_id not in records:
            return None
        entry = records[entity_id]
        if not isinstance(entry, dict):
            return {}
        return dict(entry)

    def save_entity(self, entity_id: str, fields: dict[str, Any]) -> None:
        """Persist one entity (incremental upsert on ``minisql_v1``)."""
        if self.current_strategy() == "minisql_v1":
            from storage.minisql_v1 import upsert_entity_record

            upsert_entity_record(self.sqlite_file, entity_id, fields)
            return
        data = self.load()
        records = data.setdefault("records", {})
        records[entity_id] = fields
        self.save(data)

    def delete_entity(self, entity_id: str) -> None:
        """Remove one entity from storage."""
        if self.current_strategy() == "minisql_v1":
            from storage.minisql_v1 import delete_entity_record

            delete_entity_record(self.sqlite_file, entity_id)
            return
        data = self.load()
        records = data.get("records", {})
        if isinstance(records, dict) and entity_id in records:
            del records[entity_id]
            self.save(data)

    def get_strategy(self) -> dict[str, Any]:
        if not self.strategy_file.exists():
            self._ensure_initialized()
        return json.loads(self.strategy_file.read_text(encoding="utf-8"))

    def current_strategy(self) -> str:
        return self.get_strategy().get("strategy", "versioned_provenance_v1")

    def migrate_to(self, target: str) -> None:
        """Migrate specialist storage strategy (agent-managed evolution hook)."""
        current = self.current_strategy()
        if current == target:
            return
        if target == "minisql_v1" and current == "versioned_provenance_v1":
            from storage.minisql_v1 import migrate_versioned_provenance_v1_json

            migrate_versioned_provenance_v1_json(
                self.storage_file,
                self.sqlite_file,
                category=self.category,
            )
            backup_path = self.base_dir / "storage.json.pre-minisql-v1"
            if self.storage_file.exists():
                if backup_path.exists():
                    backup_path.unlink()
                self.storage_file.rename(backup_path)
            strategy = self.get_strategy()
            strategy["strategy"] = "minisql_v1"
            strategy["last_migrated"] = datetime.now(timezone.utc).isoformat()
            self._atomic_write(self.strategy_file, strategy)
            return
        raise NotImplementedError(
            f"Storage migration from {current} to {target} not implemented in this "
            f"version of the {self.category} specialist. "
            "Edit the specialist or extend base.py to add migration logic.",
        )

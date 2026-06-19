"""Warehouse capability manifest generation and introspection."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from network.dataset_source import load_pack_dataset_source
from network.paths import NetworkPaths, framework_root
from network.warehouse import default_warehouse_path


def warehouse_manifest_path(paths: NetworkPaths) -> Path:
    """Live-root path for ``warehouse_manifest.json``."""
    return paths.root / "warehouse_manifest.json"


def example_warehouse_domains_path(example_name: str) -> Path:
    return framework_root() / "examples" / "networks" / example_name / "warehouse_domains.json"


def _infer_example_name(paths: NetworkPaths) -> str | None:
    manifest = paths.root / "network.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    raw = data.get("name")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def load_warehouse_domains_config(example_name: str) -> dict[str, Any] | None:
    """Load committed pack domain rules for an example network."""
    path = example_warehouse_domains_path(example_name)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    domains = data.get("domains")
    if not isinstance(domains, dict) or not domains:
        return None
    return data


def _dataset_block(paths: NetworkPaths, *, warehouse_relative: str) -> dict[str, Any]:
    pinned = load_pack_dataset_source(paths)
    if pinned:
        source = pinned[0]
        return {
            "id": source.get("id", "lahman"),
            "warehouse": warehouse_relative,
            "version": source.get("version", ""),
            "retrieved_from": source.get("retrieved_from", ""),
            "ref": source.get("ref", ""),
        }
    return {
        "id": "lahman",
        "warehouse": warehouse_relative,
        "version": "",
        "retrieved_from": "",
        "ref": "",
    }


def _domain_table_names(domains: dict[str, Any]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for meta in domains.values():
        if not isinstance(meta, dict):
            continue
        raw_tables = meta.get("tables")
        if not isinstance(raw_tables, list):
            continue
        for item in raw_tables:
            if not isinstance(item, str) or not item.strip():
                continue
            table = item.strip()
            if table not in seen:
                seen.add(table)
                names.append(table)
    return names


def introspect_warehouse_tables(
    warehouse_path: Path,
    table_names: list[str],
) -> dict[str, dict[str, Any]]:
    """Return column names and row counts for named tables."""
    if not warehouse_path.is_file() or not table_names:
        return {}
    conn = sqlite3.connect(f"file:{warehouse_path}?mode=ro", uri=True)
    tables: dict[str, dict[str, Any]] = {}
    try:
        for table in table_names:
            safe = table.replace('"', '""')
            info = conn.execute(f'PRAGMA table_info("{safe}")').fetchall()
            if not info:
                continue
            columns = [str(row[1]) for row in info if row[1]]
            count_row = conn.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()
            row_count = int(count_row[0]) if count_row else 0
            tables[table] = {"columns": columns, "row_count": row_count}
    finally:
        conn.close()
    return tables


def build_warehouse_manifest(
    paths: NetworkPaths,
    *,
    domains_config: dict[str, Any],
    warehouse_path: Path | None = None,
) -> dict[str, Any]:
    """Merge pack domain rules with sqlite introspection."""
    warehouse = warehouse_path or default_warehouse_path(paths)
    warehouse_relative = str(warehouse.relative_to(paths.root))
    raw_domains = domains_config.get("domains")
    domains = raw_domains if isinstance(raw_domains, dict) else {}
    table_names = _domain_table_names(domains)
    return {
        "version": "1.0",
        "dataset": _dataset_block(paths, warehouse_relative=warehouse_relative),
        "domains": domains,
        "tables": introspect_warehouse_tables(warehouse, table_names),
    }


def write_warehouse_manifest(
    paths: NetworkPaths,
    *,
    example_name: str | None = None,
    warehouse_path: Path | None = None,
) -> bool:
    """Rewrite ``warehouse_manifest.json`` when pack config and warehouse exist."""
    name = example_name or _infer_example_name(paths)
    if name is None:
        return False
    domains_config = load_warehouse_domains_config(name)
    if domains_config is None:
        return False
    warehouse = warehouse_path or default_warehouse_path(paths)
    if not warehouse.is_file():
        return False
    manifest = build_warehouse_manifest(
        paths,
        domains_config=domains_config,
        warehouse_path=warehouse,
    )
    out_path = warehouse_manifest_path(paths)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return True


def maybe_write_warehouse_manifest(paths: NetworkPaths) -> bool:
    """Idempotent manifest refresh for live roots with a warehouse DB."""
    return write_warehouse_manifest(paths)


def load_warehouse_manifest(paths: NetworkPaths) -> dict[str, Any] | None:
    path = warehouse_manifest_path(paths)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def warehouse_manifest_capabilities(paths: NetworkPaths) -> dict[str, Any] | None:
    """Summary for ``describe_network`` / ``build_network_capabilities``."""
    manifest = load_warehouse_manifest(paths)
    if manifest is None:
        return None
    dataset = manifest.get("dataset")
    dataset_id = dataset.get("id") if isinstance(dataset, dict) else None
    raw_domains = manifest.get("domains")
    domain_names = sorted(raw_domains.keys()) if isinstance(raw_domains, dict) else []
    raw_tables = manifest.get("tables")
    table_names = sorted(raw_tables.keys()) if isinstance(raw_tables, dict) else []
    try:
        rel_path = str(warehouse_manifest_path(paths).relative_to(paths.root))
    except ValueError:
        rel_path = "warehouse_manifest.json"
    return {
        "present": True,
        "path": rel_path,
        "dataset_id": dataset_id,
        "domains": domain_names,
        "tables": table_names,
    }

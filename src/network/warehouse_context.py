"""Shared warehouse domain context formatting for LLM prompts."""

from __future__ import annotations

from typing import Any


def domain_meta(manifest: dict[str, Any], domain: str) -> dict[str, Any]:
    domains = manifest.get("domains")
    if not isinstance(domains, dict):
        return {}
    meta = domains.get(domain)
    return meta if isinstance(meta, dict) else {}


def _format_alias_pattern(attr: str, spec: dict[str, Any]) -> str:
    convention = str(spec.get("convention") or "").strip()
    if convention == "career_sum" and spec.get("column"):
        return f"- {attr}: {convention} on column {spec['column']}"
    if convention == "people_column" and spec.get("column"):
        return f"- {attr}: {convention} on column {spec['column']}"
    if convention == "people_compose":
        columns = spec.get("columns") or []
        col_text = ", ".join(str(c) for c in columns) if isinstance(columns, list) else ""
        fmt = spec.get("format")
        suffix = f" ({fmt})" if fmt else ""
        return f"- {attr}: {convention} on columns {col_text}{suffix}"
    return f"- {attr}: {convention or 'alias'}"


def format_warehouse_context(manifest: dict[str, Any], domain: str) -> str:
    meta = domain_meta(manifest, domain)
    tables = meta.get("tables") or []
    grain = meta.get("grain") or []
    conventions = meta.get("conventions") or {}
    aliases = meta.get("aliases") or {}
    table_blocks = manifest.get("tables") if isinstance(manifest.get("tables"), dict) else {}

    lines = [
        "Warehouse context:",
        f"Domain: {domain}",
    ]
    grain_items = [str(item) for item in grain]
    if grain_items:
        lines.append(f"Grain: {', '.join(grain_items)}")
    if any(item in {"stint", "yearID"} for item in grain_items):
        lines.append(
            "Note: Grain includes stint/year — multiple rows per player; "
            "aggregate across all domain rows before career-level rates."
        )

    lines.append("Tables:")
    for table in tables:
        info = table_blocks.get(table) if isinstance(table_blocks, dict) else None
        cols = info.get("columns") if isinstance(info, dict) else []
        col_text = ", ".join(str(c) for c in cols) if isinstance(cols, list) else ""
        row_count = info.get("row_count") if isinstance(info, dict) else None
        row_suffix = f", {row_count} rows" if row_count is not None else ""
        lines.append(f"- {table}{row_suffix}: [{col_text}]")
    if not tables:
        lines.append("- (none)")

    lines.append("Conventions:")
    if isinstance(conventions, dict) and conventions:
        for name, rule in sorted(conventions.items()):
            lines.append(f"- {name}: {rule}")
    else:
        lines.append("- (none)")

    lines.append("Resolved alias patterns in this domain (committed code uses these):")
    if isinstance(aliases, dict) and aliases:
        for attr, spec in sorted(aliases.items()):
            if isinstance(spec, dict):
                lines.append(_format_alias_pattern(str(attr), spec))
    else:
        lines.append("- (none)")

    lines.extend(
        [
            "Execution environment:",
            "- SQLite read-only warehouse via query_warehouse(warehouse, sql, params).",
            "- Placeholder style: ? for sqlite3 parameters.",
            "- Integer aggregates stay integer; ratio/rate arithmetic should happen in Python "
            "after fetching separate aggregates unless explicitly cast.",
        ],
    )
    return "\n".join(lines)

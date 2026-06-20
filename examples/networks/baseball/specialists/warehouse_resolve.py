"""Manifest-driven Lahman warehouse resolution (baseball pack)."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from network.paths import NetworkPaths
from network.warehouse import default_warehouse_path, query_warehouse
from network.warehouse_manifest import load_warehouse_manifest

LAHMAN_PLAYER_ID = "lahman.playerID"
LAHMAN_TEAM_ID = "lahman.teamID"


def _domain_table(manifest: dict[str, Any], domain: str) -> str:
    domains = manifest.get("domains")
    if isinstance(domains, dict):
        meta = domains.get(domain)
        if isinstance(meta, dict):
            tables = meta.get("tables")
            if isinstance(tables, list) and tables:
                first = tables[0]
                if isinstance(first, str) and first.strip():
                    return first.strip()
    return "Batting"


def career_sum(
    column: str,
    player_id: str,
    warehouse: Path,
    *,
    table: str = "Batting",
) -> int:
    safe_col = column.replace('"', '""')
    safe_table = table.replace('"', '""')
    rows = query_warehouse(
        warehouse,
        f'SELECT COALESCE(SUM(CAST("{safe_col}" AS INTEGER)), 0) '
        f'FROM "{safe_table}" WHERE "playerID" = ?',
        (player_id,),
    )
    return int(rows[0][0]) if rows else 0


def team_latest_column(column: str, team_id: str, warehouse: Path) -> str | None:
    """Read one Teams column for the latest ``yearID`` row matching ``teamID``."""
    safe_col = column.replace('"', '""')
    rows = query_warehouse(
        warehouse,
        f'SELECT "{safe_col}" FROM "Teams" WHERE "teamID" = ? '
        f'ORDER BY CAST("yearID" AS INTEGER) DESC LIMIT 1',
        (team_id,),
    )
    if not rows:
        return None
    value = rows[0][0]
    if value in (None, ""):
        return None
    return str(value).strip()


def people_column(column: str, player_id: str, warehouse: Path) -> str | None:
    safe_col = column.replace('"', '""')
    rows = query_warehouse(
        warehouse,
        f'SELECT "{safe_col}" FROM "People" WHERE "playerID" = ?',
        (player_id,),
    )
    if not rows:
        return None
    value = rows[0][0]
    if value in (None, ""):
        return None
    return str(value).strip()


def people_birth_date(player_id: str, warehouse: Path) -> str | None:
    return people_compose_iso_date(
        ["birthYear", "birthMonth", "birthDay"],
        player_id,
        warehouse,
    )


def people_compose_iso_date(columns: list[str], player_id: str, warehouse: Path) -> str | None:
    if len(columns) != 3:
        return None
    safe_cols = [col.replace('"', '""') for col in columns]
    col_list = ", ".join(f'"{col}"' for col in safe_cols)
    rows = query_warehouse(
        warehouse,
        f'SELECT {col_list} FROM "People" WHERE "playerID" = ?',
        (player_id,),
    )
    if not rows:
        return None
    year, month, day = rows[0]
    if year in (None, "") or month in (None, "") or day in (None, ""):
        return None
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def career_era_weighted(player_id: str, warehouse: Path, *, table: str = "Pitching") -> str | None:
    safe_table = table.replace('"', '""')
    rows = query_warehouse(
        warehouse,
        f'SELECT COALESCE(SUM(CAST("ER" AS INTEGER)), 0), '
        f'COALESCE(SUM(CAST("IPouts" AS INTEGER)), 0) '
        f'FROM "{safe_table}" WHERE "playerID" = ?',
        (player_id,),
    )
    if not rows:
        return None
    er, ipouts = int(rows[0][0]), int(rows[0][1])
    if ipouts == 0:
        return None
    innings = ipouts / 3.0
    era = 9.0 * er / innings
    return f"{era:.3f}"


CAREER_SUM_INLINE = inspect.getsource(career_sum)
TEAM_LATEST_COLUMN_INLINE = inspect.getsource(team_latest_column)
PEOPLE_COLUMN_INLINE = inspect.getsource(people_column)
PEOPLE_BIRTH_DATE_INLINE = inspect.getsource(people_birth_date)
PEOPLE_COMPOSE_ISO_DATE_INLINE = inspect.getsource(people_compose_iso_date)
CAREER_ERA_WEIGHTED_INLINE = inspect.getsource(career_era_weighted)


@dataclass(frozen=True)
class ResolvedField:
    value: str
    computation_inline: str
    attribute: str
    column: str | None = None


def load_manifest(paths: NetworkPaths) -> dict[str, Any] | None:
    return load_warehouse_manifest(paths)


def warehouse_relative(paths: NetworkPaths, warehouse: Path) -> str:
    try:
        return str(warehouse.relative_to(paths.root))
    except ValueError:
        return str(warehouse)


def domain_aliases(manifest: dict[str, Any], domain: str) -> dict[str, dict[str, Any]]:
    domains = manifest.get("domains")
    if not isinstance(domains, dict):
        return {}
    meta = domains.get(domain)
    if not isinstance(meta, dict):
        return {}
    raw = meta.get("aliases")
    if not isinstance(raw, dict):
        return {}
    return {
        str(key).strip().lower(): value
        for key, value in raw.items()
        if isinstance(value, dict)
    }


def resolve_domain_attribute(
    attr: str,
    *,
    domain: str,
    manifest: dict[str, Any],
    player_id: str,
    warehouse: Path,
) -> ResolvedField | None:
    """Resolve one manifest alias; return None when attr is unknown for this domain."""
    key = attr.strip().lower()
    alias = domain_aliases(manifest, domain).get(key)
    if not alias:
        return None
    convention = alias.get("convention")
    if convention == "career_sum":
        column = alias.get("column")
        if not isinstance(column, str) or not column.strip():
            return None
        col = column.strip()
        table = _domain_table(manifest, domain)
        total = career_sum(col, player_id, warehouse, table=table)
        return ResolvedField(
            value=str(total),
            computation_inline=CAREER_SUM_INLINE,
            attribute=key,
            column=col,
        )
    if convention == "people_column":
        column = alias.get("column")
        if not isinstance(column, str) or not column.strip():
            return None
        col = column.strip()
        raw = people_column(col, player_id, warehouse)
        if raw is None:
            return None
        return ResolvedField(
            value=raw,
            computation_inline=PEOPLE_COLUMN_INLINE,
            attribute=key,
            column=col,
        )
    if convention == "people_compose" and alias.get("format") == "iso_date":
        columns = alias.get("columns")
        if not isinstance(columns, list):
            return None
        cols = [str(col).strip() for col in columns if str(col).strip()]
        if len(cols) != 3:
            return None
        formatted = people_compose_iso_date(cols, player_id, warehouse)
        if formatted is None:
            return None
        inline = (
            PEOPLE_BIRTH_DATE_INLINE
            if cols == ["birthYear", "birthMonth", "birthDay"]
            else PEOPLE_COMPOSE_ISO_DATE_INLINE
        )
        return ResolvedField(
            value=formatted,
            computation_inline=inline,
            attribute=key,
            column=None,
        )
    if convention == "career_era_weighted":
        table = _domain_table(manifest, domain)
        formatted = career_era_weighted(player_id, warehouse, table=table)
        if formatted is None:
            return None
        return ResolvedField(
            value=formatted,
            computation_inline=CAREER_ERA_WEIGHTED_INLINE,
            attribute=key,
            column=None,
        )
    return None


def resolve_team_domain_attribute(
    attr: str,
    *,
    domain: str,
    manifest: dict[str, Any],
    team_id: str,
    warehouse: Path,
) -> ResolvedField | None:
    """Resolve one team-scoped manifest alias (latest season row per teamID)."""
    key = attr.strip().lower()
    alias = domain_aliases(manifest, domain).get(key)
    if not alias:
        return None
    convention = alias.get("convention")
    if convention == "team_latest_column":
        column = alias.get("column")
        if not isinstance(column, str) or not column.strip():
            return None
        col = column.strip()
        raw = team_latest_column(col, team_id, warehouse)
        if raw is None:
            return None
        return ResolvedField(
            value=raw,
            computation_inline=TEAM_LATEST_COLUMN_INLINE,
            attribute=key,
            column=col,
        )
    return None


def provenance_parameters(
    *,
    player_id: str,
    paths: NetworkPaths,
    warehouse: Path | None = None,
    attribute: str | None = None,
    column: str | None = None,
) -> dict[str, str]:
    wh = warehouse or default_warehouse_path(paths)
    params: dict[str, str] = {
        LAHMAN_PLAYER_ID: player_id,
        "warehouse": warehouse_relative(paths, wh),
    }
    if attribute and attribute.strip():
        params["attribute"] = attribute.strip().lower()
    if column and column.strip():
        params["column"] = column.strip()
    return params


def team_provenance_parameters(
    *,
    team_id: str,
    paths: NetworkPaths,
    warehouse: Path | None = None,
    attribute: str | None = None,
    column: str | None = None,
) -> dict[str, str]:
    wh = warehouse or default_warehouse_path(paths)
    params: dict[str, str] = {
        LAHMAN_TEAM_ID: team_id,
        "warehouse": warehouse_relative(paths, wh),
    }
    if attribute and attribute.strip():
        params["attribute"] = attribute.strip().lower()
    if column and column.strip():
        params["column"] = column.strip()
    return params

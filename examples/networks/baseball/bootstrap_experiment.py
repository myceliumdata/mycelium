#!/usr/bin/env python3
"""Baseball bootstrap experiment — ingest Lahman, propose team canon, auto-commit.

Standalone v0 (not wired into query graph). See examples/networks/baseball/README.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_ROOT = Path(__file__).resolve().parent
DEFAULT_NETWORK_ROOT = Path.home() / "mycelium-networks" / "baseball"
DEFAULT_SEED_DIR = DEFAULT_NETWORK_ROOT / "seed"
DEFAULT_OUTPUT_DIR = DEFAULT_NETWORK_ROOT / "bootstrap"

TEAM_MVR_FIELD = "team"
BOOTSTRAP_TABLES = ("People", "Teams", "Appearances", "Batting", "Pitching", "TeamsFranchises")


@dataclass
class TableProfile:
    name: str
    columns: list[str]
    row_count: int
    sample_rows: list[dict[str, str]]


@dataclass
class BootstrapReport:
    warehouse_path: Path
    output_dir: Path
    used_llm: bool
    source_tables_used: list[str] = field(default_factory=list)
    distinct_raw_labels: int = 0
    teams_committed: int = 0
    llm_notes: str = ""
    errors: list[str] = field(default_factory=list)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _read_guide() -> str:
    return (EXAMPLE_ROOT / "guide.md").read_text(encoding="utf-8")


def _resolve_csv_dir(seed: Path) -> Path:
    if seed.is_dir():
        nested = seed / "lahman_1871-2025_csv"
        return nested if nested.is_dir() else seed
    if seed.suffix == ".zip" and seed.is_file():
        extract_to = seed.parent / "lahman_1871-2025_csv"
        if not extract_to.is_dir():
            extract_to.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(seed) as zf:
                zf.extractall(extract_to.parent)
        return extract_to
    raise FileNotFoundError(f"No Lahman CSV dir or zip at {seed}")


def _load_csv(conn: sqlite3.Connection, table: str, csv_path: Path) -> int:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return 0
        cols = [c.strip() for c in reader.fieldnames]
        safe_table = table.replace('"', '""')
        col_defs = ", ".join(f'"{c.replace(chr(34), chr(34)*2)}" TEXT' for c in cols)
        conn.execute(f'DROP TABLE IF EXISTS "{safe_table}"')
        conn.execute(f'CREATE TABLE "{safe_table}" ({col_defs})')
        placeholders = ", ".join("?" for _ in cols)
        col_list = ", ".join(f'"{c.replace(chr(34), chr(34)*2)}"' for c in cols)
        rows = 0
        batch: list[tuple[str, ...]] = []
        for row in reader:
            batch.append(tuple((row.get(c) or "").strip() for c in cols))
            if len(batch) >= 2000:
                conn.executemany(
                    f'INSERT INTO "{safe_table}" ({col_list}) VALUES ({placeholders})',
                    batch,
                )
                rows += len(batch)
                batch.clear()
        if batch:
            conn.executemany(
                f'INSERT INTO "{safe_table}" ({col_list}) VALUES ({placeholders})',
                batch,
            )
            rows += len(batch)
        conn.commit()
        return rows


def ingest_warehouse(csv_dir: Path, warehouse_path: Path) -> dict[str, int]:
    warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    if warehouse_path.is_file():
        warehouse_path.unlink()
    conn = sqlite3.connect(warehouse_path)
    counts: dict[str, int] = {}
    try:
        for table in BOOTSTRAP_TABLES:
            path = csv_dir / f"{table}.csv"
            if path.is_file():
                counts[table] = _load_csv(conn, table, path)
    finally:
        conn.close()
    return counts


def profile_tables(warehouse_path: Path) -> list[TableProfile]:
    conn = sqlite3.connect(warehouse_path)
    conn.row_factory = sqlite3.Row
    profiles: list[TableProfile] = []
    try:
        for table in BOOTSTRAP_TABLES:
            try:
                conn.execute(f'SELECT 1 FROM "{table}" LIMIT 1')
            except sqlite3.OperationalError:
                continue
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
            row_count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            samples = [
                dict(r)
                for r in conn.execute(f'SELECT * FROM "{table}" LIMIT 3')
            ]
            profiles.append(
                TableProfile(
                    name=table,
                    columns=cols,
                    row_count=int(row_count),
                    sample_rows=samples,
                ),
            )
    finally:
        conn.close()
    return profiles


def distinct_team_labels(warehouse_path: Path) -> list[tuple[str, int]]:
    conn = sqlite3.connect(warehouse_path)
    try:
        rows = conn.execute(
            '''
            SELECT TRIM("name") AS label, COUNT(DISTINCT "yearID") AS seasons
            FROM "Teams"
            WHERE TRIM(COALESCE("name", "")) != ""
            GROUP BY TRIM("name")
            ORDER BY seasons DESC, label
            ''',
        ).fetchall()
        return [(str(label), int(seasons)) for label, seasons in rows]
    finally:
        conn.close()


def _merge_llm_enrichment(
    base: dict[str, Any],
    enrichment: dict[str, Any],
) -> dict[str, Any]:
    """Overlay LLM aliases/evidence onto full heuristic team list."""
    by_name = {t["canonical_name"]: dict(t) for t in base.get("teams", [])}
    for entry in enrichment.get("teams", []):
        canonical = str(entry.get("canonical_name", "")).strip()
        if not canonical or canonical not in by_name:
            continue
        merged = by_name[canonical]
        aliases = set(merged.get("aliases") or [])
        for alias in entry.get("aliases") or []:
            text = str(alias).strip()
            if text:
                aliases.add(text)
        merged["aliases"] = sorted(aliases)
        if entry.get("source_evidence"):
            merged["source_evidence"] = entry["source_evidence"]
    base["reasoning"] = (
        f"{base.get('reasoning', '')} LLM enrichment: {enrichment.get('reasoning', '')}"
    ).strip()
    if enrichment.get("source_tables_used"):
        base["source_tables_used"] = enrichment["source_tables_used"]
    base["llm_enrichment_partial"] = len(enrichment.get("teams", [])) < len(base.get("teams", []))
    return base


def _llm_propose_teams(
    guide: str,
    profiles: list[TableProfile],
    raw_labels: list[tuple[str, int]],
) -> dict[str, Any]:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    profile_blob = []
    for p in profiles:
        profile_blob.append(
            {
                "table": p.name,
                "columns": p.columns,
                "row_count": p.row_count,
                "sample_rows": p.sample_rows[:2],
            },
        )
    all_labels = [label for label, _n in raw_labels]
    system = (
        "You are a bootstrap identity specialist for a baseball data network. "
        "Respond with JSON only — no markdown."
    )
    # Enrichment pass only — full canon list comes from heuristic enumeration.
    enrichment_sample = all_labels[:60]
    user = {
        "task": "Enrich team identity bootstrap: pick source tables and suggest aliases.",
        "network_guide": guide,
        "table_profiles": profile_blob,
        "total_distinct_labels": len(all_labels),
        "labels_to_enrich": enrichment_sample,
        "output_schema": {
            "source_tables_used": ["table names you relied on"],
            "reasoning": "which column defines fan-facing team canon and why",
            "teams": [
                {
                    "canonical_name": "exact string from labels_to_enrich",
                    "aliases": ["optional shorthand e.g. LA Dodgers for Los Angeles Dodgers"],
                    "source_evidence": "brief",
                },
            ],
        },
        "rules": [
            "Do not merge Brooklyn Dodgers with Los Angeles Dodgers.",
            "Return entries only for labels_to_enrich; aliases must not be nickname-alone (Dodgers).",
        ],
    }
    model = ChatOpenAI(model=os.getenv("MYCELIUM_BOOTSTRAP_MODEL", "gpt-4o-mini"), temperature=0)
    response = model.invoke(
        [SystemMessage(content=system), HumanMessage(content=json.dumps(user, indent=2))],
    )
    text = str(response.content).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def _heuristic_teams(raw_labels: list[tuple[str, int]]) -> dict[str, Any]:
    teams = []
    for label, seasons in raw_labels:
        teams.append(
            {
                "canonical_name": label,
                "aliases": [],
                "source_evidence": f"distinct label in Teams.name ({seasons} seasons)",
            },
        )
    return {
        "source_tables_used": ["Teams"],
        "reasoning": "No LLM — used distinct Teams.name labels as canonical (experiment fallback).",
        "teams": teams,
    }


def commit_team_registry(
    proposal: dict[str, Any],
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    entities: dict[str, Any] = {}
    alias_index: dict[str, list[str]] = {}

    for entry in proposal.get("teams", []):
        canonical = str(entry.get("canonical_name", "")).strip()
        if not canonical:
            continue
        entity_id = str(uuid.uuid4())
        entities[entity_id] = {
            "id": entity_id,
            "kind": "team",
            "bind_values": {TEAM_MVR_FIELD: canonical},
            "validation_state": "validated",
            "source": "bootstrap_experiment_v0",
            "provenance": {
                "at": _utc_now(),
                "source_evidence": entry.get("source_evidence", ""),
            },
        }
        keys = {canonical.lower()}
        for alias in entry.get("aliases") or []:
            text = str(alias).strip()
            if text:
                keys.add(text.lower())
        for key in keys:
            alias_index.setdefault(key, []).append(entity_id)

    registry = {
        "kind": "team",
        "mvr": {"bind_fields": [TEAM_MVR_FIELD]},
        "entities": entities,
        "alias_index": alias_index,
        "bootstrap_proposal": proposal,
        "committed_at": _utc_now(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "team_registry.json"
    out_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return registry, alias_index


def run_bootstrap(
    *,
    seed: Path,
    network_root: Path,
    use_llm: bool,
) -> BootstrapReport:
    output_dir = network_root / "bootstrap"
    warehouse_path = network_root / "warehouse" / "lahman.sqlite"
    guide = _read_guide()
    csv_dir = _resolve_csv_dir(seed)

    ingest_counts = ingest_warehouse(csv_dir, warehouse_path)
    profiles = profile_tables(warehouse_path)
    raw_labels = distinct_team_labels(warehouse_path)

    report = BootstrapReport(
        warehouse_path=warehouse_path,
        output_dir=output_dir,
        used_llm=False,
        distinct_raw_labels=len(raw_labels),
    )
    report.source_tables_used = [k for k, v in ingest_counts.items() if v > 0]

    proposal: dict[str, Any]
    base = _heuristic_teams(raw_labels)
    if use_llm and os.getenv("OPENAI_API_KEY"):
        try:
            enrichment = _llm_propose_teams(guide, profiles, raw_labels)
            proposal = _merge_llm_enrichment(base, enrichment)
            report.used_llm = True
            report.llm_notes = str(proposal.get("reasoning", ""))
        except Exception as exc:  # noqa: BLE001 — experiment captures failures
            report.errors.append(f"LLM failed: {exc}")
            proposal = base
            report.llm_notes = proposal.get("reasoning", "")
    else:
        if use_llm and not os.getenv("OPENAI_API_KEY"):
            report.errors.append("OPENAI_API_KEY not set — heuristic fallback")
        proposal = base
        report.llm_notes = proposal.get("reasoning", "")

    registry, _ = commit_team_registry(proposal, output_dir)
    report.teams_committed = len(registry.get("entities", {}))
    report.source_tables_used = list(proposal.get("source_tables_used", report.source_tables_used))

    summary = {
        "experiment": "baseball-bootstrap-v0",
        "at": _utc_now(),
        "ingest_counts": ingest_counts,
        "report": {
            "warehouse_path": str(warehouse_path),
            "output_dir": str(output_dir),
            "used_llm": report.used_llm,
            "source_tables_used": report.source_tables_used,
            "distinct_raw_labels": report.distinct_raw_labels,
            "teams_committed": report.teams_committed,
            "llm_notes": report.llm_notes,
            "errors": report.errors,
        },
        "sample_teams": list(registry.get("entities", {}).values())[:5],
        "sample_aliases": dict(list(registry.get("alias_index", {}).items())[:8]),
    }
    (output_dir / "bootstrap_report.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Baseball Lahman bootstrap experiment (v0)")
    parser.add_argument(
        "--seed",
        type=Path,
        default=DEFAULT_SEED_DIR / "lahman_1871-2025_csv.zip",
        help="Lahman zip or extracted CSV directory",
    )
    parser.add_argument(
        "--network-root",
        type=Path,
        default=DEFAULT_NETWORK_ROOT,
        help="Live network root for warehouse + bootstrap output",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use OpenAI to propose canonical teams (requires OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Force heuristic distinct-name fallback",
    )
    args = parser.parse_args()
    use_llm = args.llm and not args.no_llm
    report = run_bootstrap(
        seed=args.seed,
        network_root=args.network_root,
        use_llm=use_llm,
    )
    print(json.dumps({
        "warehouse": str(report.warehouse_path),
        "output": str(report.output_dir),
        "used_llm": report.used_llm,
        "teams_committed": report.teams_committed,
        "distinct_raw_labels": report.distinct_raw_labels,
        "errors": report.errors,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
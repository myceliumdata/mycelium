# Baseball warehouse capability manifest (M2a)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **After M1c + polish nits** in tree.

**Priority:** Unlock layer 3 — specialists discover **what they may read** from a machine-generated manifest, not hand-listed `attribute_map` entries for every Lahman column.

**Parent:** [`docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md`](../../docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md)

**Principles:**

- **Do not** add hundreds of keys to `categories.json` `attribute_map`.
- **Do** generate `warehouse_manifest.json` at bootstrap/sync from `warehouse/lahman.sqlite`.
- **Coarse ontology unchanged** — manifest links domains to tables; `categories.json` stays batting/bio/pitching/team_season.
- **Pack-only Lahman table rules** may live in `examples/networks/baseball/` (manifest template or domain map).
- **Do not edit `TODO.md`.**

---

## Objective

After refresh/sync on a baseball root with a warehouse DB, a **`warehouse_manifest.json`** exists and **`describe_network`** exposes a summary so MCP clients (and specialists) know tables, grains, and domain ownership.

**Non-goal this slice:** generic stat resolver (M2b), LLM codegen (M3), changing specialist compute behavior beyond reading manifest if needed for tests.

---

## Manifest shape (locked v1)

Write under `<network_root>/warehouse_manifest.json`:

```json
{
  "version": "1.0",
  "dataset": {
    "id": "lahman",
    "warehouse": "warehouse/lahman.sqlite",
    "version": "v2025.1",
    "retrieved_from": "https://github.com/myceliumdata/lahman-seed.git",
    "ref": "v2025.1"
  },
  "domains": {
    "batting": {
      "specialist": "batting_specialist",
      "tables": ["Batting"],
      "grain": ["playerID", "yearID", "stint", "teamID", "lgID"],
      "conventions": {
        "career_sum": "SUM({column}) GROUP BY playerID"
      }
    },
    "bio": {
      "specialist": "bio_specialist",
      "tables": ["People"],
      "grain": ["playerID"]
    },
    "pitching": {
      "specialist": "pitching_specialist",
      "tables": ["Pitching"],
      "grain": ["playerID", "yearID", "stint", "teamID", "lgID"]
    },
    "team_season": {
      "specialist": "team_season_specialist",
      "tables": ["Teams"],
      "grain": ["yearID", "teamID", "lgID"]
    }
  },
  "tables": {
    "Batting": {
      "columns": ["playerID", "yearID", "HR", "..."],
      "row_count": 128598
    }
  }
}
```

- **`tables`:** from `PRAGMA table_info` + `SELECT COUNT(*)` per table present in sqlite (cap listed tables to domains + core tables if needed for perf on full Lahman).
- **`dataset`:** pin from `seed.source.json` / bootstrap fetch summary when available.
- **Domain map:** start from committed pack config in `examples/networks/baseball/warehouse_domains.json` (create) — manifest generator merges introspection + static domain rules.

---

## Implement

### 1 — Pack config

**File:** `examples/networks/baseball/warehouse_domains.json` — domain → tables, specialist, grain, conventions (v1 batting/bio/pitching/team_season only).

### 2 — Generator

**Framework or pack:** prefer `examples/networks/baseball/bootstrap_handlers/` or `src/network/warehouse_manifest.py` (framework) called from:

- `LahmanSeedHandler` after warehouse ingest, and  
- `install_pack_ontology_from_example` / `refresh --sync-only` when warehouse exists  

Idempotent rewrite of `warehouse_manifest.json`.

### 3 — Introspection

**`src/network/introspection.py`:** `build_network_capabilities()` includes `warehouse_manifest` summary (dataset id, domain names, table list) when file present. Full manifest readable from disk path documented in payload.

### 4 — Tests

- Minimal fixture sqlite or mock: manifest written with expected domains/tables.
- `build_network_capabilities()` includes manifest summary on baseball fixture root.
- M1b/M1c smoke unchanged.

### 5 — Docs

- Short note in `examples/networks/baseball/README.md` — manifest purpose, not operator-edited.

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_warehouse_manifest.py -q   # new
```

---

## For Grok + Paul (output.md)

- M2a done; queue **M2b** generic resolver.
- Note if full Lahman introspection is slow — document table cap policy.

**Suggested commit message:**

```
baseball: warehouse capability manifest + describe_network surfacing (M2a)
```
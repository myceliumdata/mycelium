# Baseball batting specialist + computation-centric provenance (M1b)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting). **Depends on M1a** (`2026-06-19-0900-baseball-committed-ontology-m1a`) merged or present in tree.

**Priority:** First warehouse-backed deliver after baseball ontology. Program slice #5: resolve player → one derived stat with locked provenance shape.

**Parent:** [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md); M1a ontology (`career_hr` → `batting`).

**Principles:**

- **Framework generic** — computation version writer + optional warehouse SQL helper; **no Lahman table names in `src/agents/supervisor.py`**.
- **Baseball logic in pack** — `examples/networks/baseball/specialists/batting_specialist.py` + `bootstrap_handlers/lahman_common.py` reuse.
- **Compute on read** — no bootstrap materialization of career stats; cache in specialist storage after first deliver.
- **CRM unchanged** — research provenance path untouched; new writer is additive.
- **Do not edit `TODO.md`.**

---

## Objective

End-to-end: resolve a bootstrap fixture player → step 2 with `requested_attributes: ["career_hr"]` → `found` with correct value, and with `provenance=true` versions include **`sources[]` (dataset pin) + `computation` (inline code) + `parameters` (`lahman.playerID`)**.

**Locked first attribute:** `career_hr` only (other batting attrs may work incidentally; tests gate on `career_hr`).

---

## Locked provenance shape (Paul, June 2026)

Per [`2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md):

```json
{
  "id": "v1",
  "at": "<iso8601>",
  "status": "found",
  "value": "<string>",
  "actor": {
    "kind": "specialist",
    "category": "batting",
    "specialist": "batting_specialist"
  },
  "sources": [
    {
      "kind": "dataset",
      "id": "lahman",
      "version": "v2025.1",
      "retrieved_from": "https://github.com/myceliumdata/lahman-seed.git",
      "ref": "v2025.1"
    }
  ],
  "computation": {
    "language": "python",
    "inline": "<exact source string executed — see below>"
  },
  "parameters": {
    "lahman.playerID": "<playerID>"
  }
}
```

- **No** `confidence` required for computed versions.
- **No** table/column names in provenance (detail lives in `computation.inline`).
- **Dataset pin** — read `examples/networks/baseball/seed.source.json` at runtime (`repo`, `ref`); map to `id: lahman`, `version: ref`, `retrieved_from: repo`. Generic helper in framework; Lahman id string only in pack constant if needed.

### Locked `computation.inline` for `career_hr` (pack)

Store the **actual** Python that ran (multi-line string). Suggested canonical body (adjust only if equivalent):

```python
import sqlite3
from pathlib import Path

def career_hr(player_id: str, warehouse: Path) -> int:
    conn = sqlite3.connect(warehouse)
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(HR), 0) FROM Batting WHERE playerID = ?",
            (player_id,),
        ).fetchone()
        return int(row[0] if row else 0)
    finally:
        conn.close()
```

Provenance `inline` should be this source (or the exact inlined equivalent the specialist executes). Do not store secrets.

---

## Implement

### 1 — Framework: computed version writer

Add `src/agents/specialists/computed.py` (or extend `fields.py`) with:

- `build_computed_version_body(*, value, actor, sources, computation, parameters, at) -> dict`
- `append_computed_version(entry, body) -> dict` — uses existing `append_version`

Add `SpecialistAgent.write_computed_fields(entity_id, specs: dict[str, ComputedFieldSpec])` **or** `write_computed_field(...)` that writes `found` versions with full body (sources, computation, parameters) — separate from `write_fields` / research shape.

**Pass-through:** existing `field_snapshot(..., include_provenance=True)` must return new keys inside `versions[]` unchanged (already deep-copies).

### 2 — Framework: dataset source helper (v1 — no manifest)

`src/network/dataset_source.py` (names flexible):

- `load_pack_dataset_source(paths: NetworkPaths) -> list[dict] | None` — if `seed.source.json` exists and `type==git`, return one `kind: dataset` dict (`id` from repo basename or `"lahman"` only when manifest/network name is baseball — **prefer**: read optional `"dataset_id": "lahman"` from `seed.source.json`; if absent, derive from repo URL last segment without `.git`).
- For baseball example, add to `seed.source.json`: `"dataset_id": "lahman"` (pack file edit).

### 3 — Framework: warehouse read helper (generic)

`src/network/warehouse.py`:

- `default_warehouse_path(paths, relative="warehouse/lahman.sqlite")` — path under `paths.root`; relative default overridable by caller.
- `query_warehouse(path: Path, sql: str, params: tuple) -> list[tuple]` — sqlite3, read-only; raise clear error if file missing.

No Lahman-specific SQL in this module.

### 4 — Framework: registry `source_keys` bridge (generic)

`src/agents/registry_bridge.py` or method on entity registry consumer:

- `entity_source_key(entity_id, key: str, *, record_type: str | None = None) -> str | None` — load `RegistryEntity`, return `source_keys.get(key)`.

Used by pack specialist; key name `lahman.playerID` stays in **pack** as constant (reuse `LAHMAN_PLAYER_ID` from `lahman_common.py`).

### 5 — Pack: `batting_specialist.py`

**File:** `examples/networks/baseball/specialists/batting_specialist.py`

- Subclass `SpecialistAgent` (`category="batting"`, `agent_name="batting_specialist"`).
- Module singleton `AGENT`.
- `run(state)`:
  1. Resolve `entity_id`, `target_fields` / owned attrs (same patterns as factory template).
  2. For each requested field: if cached `found` in storage → return.
  3. On miss for `career_hr`: load `lahman.playerID` via bridge; query warehouse `SUM(HR)`; build provenance; `write_computed_field`.
  4. Unknown batting fields → `na` or skip (not research).
  5. Return graph result consistent with other specialists (`response_found` / assemble contract).

**No Tavily / research** in this specialist for M1b.

### 6 — Pack install on refresh

Extend M1a pack install (or add parallel hook):

- Copy `examples/networks/baseball/specialists/*.py` → `<network_root>/specialists/` when present (overwrite factory stub for `batting_specialist`).
- Ensure `agent_registry.json` entry for `batting_specialist` uses `entrypoint` that resolves to pack module (`batting_specialist` function or `AGENT.run` — match how registry loads `specialists_dir` py files).

Do **not** copy CRM specialists from pack.

### 7 — Test fixtures: `Batting.csv`

Extend minimal Lahman fixtures used in tests / smoke:

**`tests/test_lahman_seed_handler.py` / `tests/test_example_network.py` / `bin/smoke-baseball-e2e` fixture builders** — add `Batting.csv`:

```csv
playerID,yearID,stint,teamID,lgID,G,AB,R,H,2B,3B,HR,RBI,SB,CS,BB,SO,IBB,HBP,SH,SF,GIDP
aaronha01,1957,1,BRO,NL,1,4,0,2,0,0,1,1,0,0,0,0,0,0,0,0,0
aaronha01,1958,1,LAN,NL,1,4,0,2,0,0,2,2,0,0,0,0,0,0,0,0,0
```

Expected `career_hr` = **`3`** for fixture `aaronha01`.

Ensure `lahman_common.BOOTSTRAP_TABLES` already includes `Batting` (it does) — warehouse ingest picks up new CSV.

### 8 — Tests

**`tests/test_baseball_batting_specialist.py`** (new):

| Test | Assert |
|------|--------|
| `career_hr` compute | Fixture root → bootstrap → resolve Hank Aaron → deliver `career_hr` → `found`, value `"3"` |
| Provenance shape | `provenance=true` on step 2 → `career_hr` version has `sources[0].kind==dataset`, `computation.inline` non-empty, `parameters["lahman.playerID"]=="aaronha01"` |
| Cache hit | Second deliver returns same value without recomputing (optional: audit or storage read) |
| Missing warehouse | Graceful `na` or error message — no crash |
| CRM regression | `./bin/ci-local` green |

**Extend `bin/smoke-baseball-e2e`:**

After player identity deliver, step 2 with `requested_attributes: ["career_hr"]` + `provenance: true` → assert outcome `found`, `career_hr==3`, provenance keys present.

### 9 — Docs

- `examples/networks/baseball/README.md` — example step-2 query JSON for `career_hr`, provenance note, link to conversation doc.
- Optional: `examples/networks/baseball/queries/03-career-hr.json` (if queries dir exists or create one file).

---

## Non-goals

- `bio_specialist` web research / extraction provenance.
- `birth_date` warehouse read (follow-up slice).
- Dataset manifest catalog (deferred TODO).
- `content_hash` on `computation.uri`.
- Fielding, pitching, team_season specialists.
- Bootstrap-time stat materialization.
- `TODO.md` edits.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md)
- M1a prompt / `examples/networks/baseball/categories.json`
- `src/agents/specialists/agent.py`, `fields.py`, `snapshots.py`
- `src/agents/registry.py` — dynamic load from `specialists_dir`
- `examples/networks/baseball/bootstrap_handlers/lahman_common.py`
- `tests/test_query_provenance.py` — provenance API patterns
- `bin/smoke-baseball-e2e`

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_baseball_batting_specialist.py -q
./bin/smoke-baseball-e2e
```

Manual (optional):

```bash
./bin/baseball-query '{"delivery_id":"<D>", "requested_attributes": ["career_hr"], "provenance": true}'
```

---

## For Grok + Paul (output.md)

- Mark M1b done in TODO when approved.
- Note live-root refresh / `--sync-only` to pick up pack `batting_specialist.py`.
- Suggest next: `bio_specialist` warehouse `birth_date` **or** web supplemental with full `computation` on research path.

**Suggested commit message:** `baseball: batting specialist career_hr + computation provenance (M1b)`
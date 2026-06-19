# Baseball bio specialist — raw warehouse read (M1c)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting). **Depends on M1b** (`2026-06-19-1000-baseball-batting-specialist-m1b`) merged or present in tree.

**Priority:** Paul’s progression — **raw Lahman read fully working** before hand-testing aggregates (`career_hr`). M1b shipped aggregate + framework plumbing; this slice adds the **raw** path on the same provenance contract.

**Parent:** [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md); M1a ontology (`birth_date` → `bio`).

**Principles:**

- **Reuse M1b framework** — `write_computed_field`, `load_pack_dataset_source`, `query_warehouse`, `entity_source_key`, pack `specialists/` copy on install. **Do not re-add** those modules unless a gap is found.
- **Pack-only Lahman logic** — SQL and `LAHMAN_PLAYER_ID` in `examples/networks/baseball/specialists/bio_specialist.py` (import constant from `lahman_common` if exported).
- **Raw read** — single-row `People` lookup; no `SUM`, no web research, no Tavily.
- **Same provenance envelope** — `sources[]` (dataset pin) + `computation.inline` (actual code) + `parameters` (`lahman.playerID`). Value is still produced by code, not a magic column citation.
- **Do not edit `TODO.md`.**

---

## Objective

End-to-end: resolve fixture Hank Aaron → step 2 with `requested_attributes: ["birth_date"]` → `found` with **`1934-02-05`**, and `provenance=true` shows dataset + inline computation + `parameters`.

**Locked first attribute:** `birth_date` only (other bio attrs may follow the same pattern later).

---

## Locked behavior

### Value

Format **`YYYY-MM-DD`** from Lahman `People` columns `birthYear`, `birthMonth`, `birthDay`:

- Zero-pad month and day to two digits.
- If any component missing/empty → `status: na` with reason (do not guess).

### Fixture (all minimal Lahman fixture builders)

Extend `People.csv` header and row for `aaronha01`:

```csv
ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut
1,aaronha01,Hank,Aaron,1934,2,5,
```

**Expected `birth_date`:** `1934-02-05`

Update every copy of the minimal fixture helper:

- `tests/test_baseball_batting_specialist.py` (`_write_minimal_lahman_fixture`)
- `tests/test_baseball_pack_ontology.py`
- `tests/test_lahman_seed_handler.py`
- `tests/test_example_network.py`
- `bin/smoke-baseball-e2e`

Keep existing `Batting.csv` rows (M1b `career_hr==3` must stay green).

### Provenance `computation.inline` (pack)

Store the **actual** Python executed, e.g.:

```python
import sqlite3
from pathlib import Path

def birth_date(player_id: str, warehouse: Path) -> str | None:
    conn = sqlite3.connect(warehouse)
    try:
        row = conn.execute(
            "SELECT birthYear, birthMonth, birthDay FROM People WHERE playerID = ?",
            (player_id,),
        ).fetchone()
        if row is None:
            return None
        year, month, day = row
        if year in (None, "") or month in (None, "") or day in (None, ""):
            return None
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    finally:
        conn.close()
```

Dataset `sources[]` — same helper as M1b (`load_pack_dataset_source`).

---

## Implement

### 1 — Pack: `bio_specialist.py`

**File:** `examples/networks/baseball/specialists/bio_specialist.py`

Mirror `batting_specialist.py` structure:

- `BioSpecialist(SpecialistAgent)` with `category="bio"`, `agent_name="bio_specialist"`.
- `AGENT` singleton + `bio_specialist(state)` graph entrypoint.
- `run()`: cache hit → return; miss on `birth_date` → warehouse read → `write_computed_field`; other bio fields → `na` for M1c (no research).
- Missing warehouse file / missing `lahman.playerID` → graceful `na`, no crash.

### 2 — Pack install

M1b extended `pack_ontology` to copy `specialists/*.py` — ensure `bio_specialist.py` is copied on refresh/sync-only (no framework change unless copy is broken).

### 3 — Tests

**`tests/test_baseball_bio_specialist.py`** (new):

| Test | Assert |
|------|--------|
| `birth_date` deliver | Fixture refresh → resolve Aaron → step 2 → `found`, `birth_date==1934-02-05` |
| Provenance | `provenance=true` → `sources[0].kind==dataset`, `computation.inline` non-empty, `parameters["lahman.playerID"]=="aaronha01"` |
| Cache | Second deliver same value |
| Missing birth parts | People row without birthMonth → `na` for `birth_date` (small inline fixture variant) |
| CRM / M1b regression | `./bin/ci-local` green; `tests/test_baseball_batting_specialist.py` still passes |

### 4 — Smoke

**`bin/smoke-baseball-e2e`:** add scenario after identity deliver:

- Step 2 `requested_attributes: ["birth_date"]`, `provenance: true`
- Assert `found`, `birth_date==1934-02-05`, provenance keys present

Keep `career_hr==3` scenario (M1b).

### 5 — Docs

- `examples/networks/baseball/README.md` — raw `birth_date` example (step 1 + step 2 JSON).
- `examples/networks/baseball/queries/04-birth-date.json` — copy-paste query pack.

---

## Non-goals

- Web bio / Tavily / research provenance migration.
- `bats`, `throws`, `birth_city`, or other bio attrs (follow-ups).
- Aggregates (`career_hr` — already M1b).
- Dataset manifest, `content_hash`, ontology generator.
- Framework changes beyond what M1b already shipped unless required for bio path.
- `TODO.md` edits.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md)
- `examples/networks/baseball/specialists/batting_specialist.py` — pack pattern to mirror
- `src/agents/specialists/agent.py` — `write_computed_field`
- `src/network/warehouse.py`, `src/network/dataset_source.py`, `src/agents/registry_bridge.py`
- `tests/test_baseball_batting_specialist.py`
- M1b `output.md` in `prompts/cursor/done/2026-06-19-1000-baseball-batting-specialist-m1b/`

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_baseball_bio_specialist.py tests/test_baseball_batting_specialist.py -q
./bin/smoke-baseball-e2e
```

---

## For Grok + Paul (output.md)

- Mark **M1c** done in `TODO.md` when approved.
- **Hand-test order:** `birth_date` (raw) on full Lahman, then `career_hr` (aggregate).
- Live root: `./bin/refresh-example-network baseball --sync-only`.

**Suggested commit message:**

```
baseball: bio specialist birth_date raw read + provenance (M1c)
```
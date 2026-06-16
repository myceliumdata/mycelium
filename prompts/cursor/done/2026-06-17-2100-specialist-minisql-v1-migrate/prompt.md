# Specialist storage — implement `migrate_to("minisql_v1")`

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Program:** Storage evolution (specialist → entity). **Slice 2 of 5.** Map: `docs/plans/storage-evolution-program.md`

**Depends on:** Slice 1 approved (`2026-06-17-1900-specialist-optimize-storage-check`).

**Context:** Specialist JSON stores (`agents/<category>/storage.json`) rewrite the full file on every save. Baseball-scale research/bootstrap exposed O(n) JSON cost. Slice 1 adds threshold-gated `optimize_storage()` on `SpecialistAgent`. **This slice** implements real migration to **`minisql_v1`** (SQLite backend) for specialist category storage, reusable later by entity stores (slice 4).

**After this slice:** Paul + Grok run **timing test 3** (manual) before releasing slice 4 from `hold/`.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| M1 | **Strategy name:** `minisql_v1` (matches `storage_strategy.json` `next_candidates`). |
| M2 | **Trigger:** existing `_maybe_optimize_storage()` before `write_fields` / `bootstrap_entity` when slice-1 threshold crossed. |
| M3 | **Idempotent:** if already `minisql_v1`, `migrate_to` and `optimize_storage` are no-ops. |
| M4 | **Protocol boundary unchanged:** `read_fields` / `write_fields` / admin snapshots must return the same shapes post-migration. |
| M5 | **JSON backup:** on successful migration, rename `storage.json` → `storage.json.pre-minisql-v1` (do not delete). |
| M6 | **Shared migration module:** implement SQLite primitives in a shared module (e.g. `src/storage/minisql_v1.py`) so slice 4 can reuse for entity grains. |
| M7 | **v1 schema pragmatism:** SQLite rows may store versioned field blobs as JSON text keyed by `(entity_id, field_name)` — optimize I/O first; full normalization is follow-up. |
| M8 | **CRM regression:** 15-entity CRM refresh/capstones unchanged in behavior. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/plans/storage-evolution-program.md`
- `prompts/cursor/done/2026-06-17-1900-specialist-optimize-storage-check/` (after approved)
- `src/agents/specialists/base.py` — `SpecialistStorage`
- `src/agents/specialists/agent.py`
- `src/agents/specialists/fields.py` — versioned field semantics (read paths must still work)
- `tests/test_specialist_agent_class.py`
- `tests/test_example_network_capstones.py`

---

## Architecture target

```
SpecialistAgent.write_fields
    → _maybe_optimize_storage()
        → migrate_to("minisql_v1")  [when threshold crossed]
            → SpecialistStorage.migrate_to
                → minisql_v1.migrate_specialist_json(...)  [shared]
    → storage.load/save (SQLite-backed when strategy=minisql_v1)
```

**SQLite location:** `<agents>/<category>/storage.sqlite` (or `minisql.sqlite` — pick one, document in architecture).

**`storage_strategy.json` after migration:**

- `strategy`: `minisql_v1`
- `last_migrated`: ISO timestamp
- preserve/readable `upgrade_path` history

---

## Implement

### 1 — Shared `minisql_v1` module

Add `src/storage/minisql_v1.py` (or `src/agents/specialists/minisql_v1.py` if you prefer colocation — prefer **`src/storage/`** for entity reuse):

- `migrate_versioned_provenance_v1_json(json_path, sqlite_path, *, category: str) -> None`
- `load_records(sqlite_path) -> dict` compatible with current `records` shape OR adapter inside `SpecialistStorage.load`
- `save_records(sqlite_path, records: dict) -> None` with incremental / transactional write (avoid full-file JSON dump)
- Unit tests with tmp_path fixture (no full Lahman)

### 2 — `SpecialistStorage.migrate_to("minisql_v1")`

Replace `NotImplementedError` path for `versioned_provenance_v1` → `minisql_v1`:

1. Load existing `storage.json` if present
2. Create/populate SQLite
3. Rename JSON backup
4. Update `storage_strategy.json`

If `storage.json` missing but strategy is v1, initialize empty SQLite.

### 3 — `SpecialistStorage.load` / `save`

Branch on `current_strategy()`:

- `versioned_provenance_v1` — existing JSON path (unchanged)
- `minisql_v1` — SQLite path via shared module

Ensure graph research paths using `AGENT.storage` / `get_specialist_storage()` see migrated data.

### 4 — Threshold integration

Confirm slice-1 `optimize_storage()` triggers migration on first write at/above threshold. Add smoke test:

- Seed JSON store with **threshold** entities (use `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD=5` in test)
- One `write_fields` → strategy becomes `minisql_v1`
- Second read/write roundtrip preserves values + version structure

### 5 — Tests

| Test | Requirement |
|------|-------------|
| `test_minisql_v1_migrates_json_backup` | Backup file exists; strategy updated |
| `test_minisql_v1_read_write_roundtrip` | Field values + `versions[]` survive migrate + subsequent write |
| `test_optimize_storage_triggers_migration` | End-to-end via `SpecialistAgent` instance |
| CRM capstones / Program 2 matrix | Green — no behavior change at CRM scale (under threshold) |
| `test_specialist_storage_boundaries` | Still green |

Optional (if fast): mock Lahman-sized JSON with 60 synthetic records in tmp_path — assert migration completes under CI time budget.

### 6 — Docs

- `docs/architecture.md` addendum: `minisql_v1` specialist storage; shared module; threshold migration; JSON backup.
- **Do not** edit `TODO.md`.

---

## Out of scope

- Entity registry `entities/<grain>.json` (slice 4 — reuse shared module only)
- Baseball bootstrap batch/deferred save (slice 4)
- Query graph changes
- Removing JSON strategy entirely (both backends coexist)

---

## Scope boundaries (strict)

**You may modify:**

- `src/storage/minisql_v1.py` (new shared module)
- `src/agents/specialists/base.py` — `SpecialistStorage.load` / `save` / `migrate_to`
- `src/agents/specialists/agent.py` (only if needed for migration integration; avoid policy changes from slice 1)
- `tests/test_specialist_agent_class.py`, new `tests/test_minisql_v1*.py` or `tests/test_specialist_minisql_v1.py`
- `docs/architecture.md` (minimal addendum only)

**Out of scope (do not touch):**

- `TODO.md` (Grok + Paul only)
- `src/agents/entity_registry.py`, bootstrap handlers, `run_network_bootstrap`
- CRM specialist graph bodies — behavior must stay identical at CRM scale (under threshold)
- Entity store / deferred save (slice 4)
- Changing `optimize_storage()` threshold policy (slice 1)

If changes outside this scope seem necessary: **stop**, document in `output.md`, do not implement.

---

## Success criteria

1. `migrate_to("minisql_v1")` works for `SpecialistStorage`.
2. Post-migration `read_fields` / `write_fields` correct for bind + researched fields.
3. Shared `minisql_v1` module exists for slice 4 reuse.
4. Threshold-triggered migration tested.
5. `./bin/ci-local` green.
6. CRM capstones + Program 2 matrix green.

---

## Deliverables

Per `WORKFLOW.md`:

- `prompts/cursor/done/2026-06-17-2100-specialist-minisql-v1-migrate/prompt.md`
- `output.md` with verification counts + **For Grok + Paul**:
  - Note: Paul + Grok run **timing test 3** per `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` (Cursor does not run Lahman benchmark in CI)
  - Grok/Paul move slice 4 from `hold/` → `next/` after test 3 recorded
- Suggested commit message: `feat(storage): minisql_v1 specialist migration behind optimize_storage threshold`
- **Do not commit or push**

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: timing test 3 gate; slice 4 release from hold.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-17-2100-specialist-minisql-v1-migrate/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul **"slice ready for review"**

---

## Next (manual gate)

**Slice 3 — Paul + Grok:** timing test 3 (`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`). Then move `hold/2026-06-17-2300-entity-registry-storage-evolution.md` → `next/`.
# Specialist minisql_v1 — incremental per-entity writes

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** **Before** bootstrap progress slice (`2355`) and before **timing test 6** (post-fix baseball benchmark). This is the missing perf fix slice 2 review flagged but did not queue.

**Context:** `minisql_v1` specialist storage uses SQLite, but `save_payload()` still **deletes and re-inserts every row** on each `write_fields` — same semantics as rewriting `storage.json`. Lahman bootstrap does ~24k new-player binds × 2 specialists → **O(n²)** SQLite + JSON work. Entity deferred flush (slice 4) fixed registry I/O; **specialists remain the dominant cost**.

**Goal:** Per bind, **upsert one entity's field rows only** (O(1) amortized I/O). Preserve full-payload load/save for migration, tests, and explicit bulk callers.

---

## Locked decisions (Paul + Grok, June 2026)

| # | Decision |
|---|----------|
| I1 | **Incremental path is default** for `minisql_v1` on the hot `write_fields` / `read_fields` path. |
| I2 | **Keep `save_payload` full replace** for migration (`migrate_versioned_provenance_v1_json`), tests that bulk-save, and any caller passing a full document — document when each path is used. |
| I3 | **Upsert semantics** — `INSERT OR REPLACE` (or equivalent) on `entity_records` + `field_records` for the touched `entity_id` only; update `storage_meta.last_updated`; do **not** `DELETE FROM` entire tables on incremental writes. |
| I4 | **`write_fields` loads one entity** when strategy is `minisql_v1` (not full `load_payload`). **`read_fields`** already scopes to one entity — use incremental load there too if still loading full payload today. |
| I5 | **Rollback in `write_bind_fields_multi`** — snapshot **only the entity row(s)** being written per category, not `deepcopy(storage.load())` of the full store. Restore via per-entity upsert on failure. |
| I6 | **No schema version bump** — same `minisql_v1` tables; behavior change only. Existing migrated SQLite files remain valid. |
| I7 | **CRM regression** — 15-entity refresh, capstones, `test_specialist_minisql_v1.py` green; add tests proving incremental behavior. |
| I8 | **Entity store unchanged** — `save_entities_document` full replace is a separate follow-up; out of scope here. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `prompts/cursor/done/2026-06-17-2100-specialist-minisql-v1-migrate/review.md` — honest limit #1 (full replace)
- `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`
- `src/storage/minisql_v1.py` — `load_payload`, `save_payload`, schema
- `src/agents/specialists/base.py` — `load`, `save`
- `src/agents/specialists/agent.py` — `write_fields`, `read_fields`
- `src/agents/specialists/agent.py` — `write_bind_fields_multi` (rollback snapshots)
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py` — hot path
- `tests/test_specialist_minisql_v1.py`

---

## Problem (today)

```python
# write_fields (every bind)
data = self.storage.load()          # read ALL entities + parse ALL field JSON
...
self.storage.save(data)             # save_payload: DELETE ALL → INSERT ALL
```

```131:145:src/storage/minisql_v1.py
        conn.execute("DELETE FROM field_records")
        conn.execute("DELETE FROM entity_records")
        for entity_id, fields in records.items():
            ...
```

**Expected after this slice:**

```python
# write_fields (minisql_v1)
record = self.storage.load_entity(entity_id)   # one entity
...
self.storage.save_entity(entity_id, record)    # upsert that entity only
```

---

## Implement

### 1 — Incremental APIs in `src/storage/minisql_v1.py`

Add (names flexible; keep module cohesive):

- `load_entity_record(sqlite_path, entity_id) -> dict[str, Any]` — field_name → versioned blob; `{}` if missing.
- `upsert_entity_record(sqlite_path, entity_id, fields: dict[str, Any], *, version: str = "1.0", created_by: str | None = None) -> None` — transactional upsert for one entity; bump `last_updated` in `storage_meta`.
- `delete_entity_record(sqlite_path, entity_id) -> None` — optional; for rollback if entity did not exist before write.

Refactor `save_payload` to call a shared `_write_all_records(conn, records)` helper so bulk and incremental paths share insert logic — avoid duplication.

**Do not** run `executescript(_SCHEMA)` on every incremental write (only ensure schema once at open/migrate). Today `save_payload` runs it every save — fix that as part of this slice (schema once per connection or `CREATE IF NOT EXISTS` guard without full script replay).

### 2 — `SpecialistStorage` (`src/agents/specialists/base.py`)

When `current_strategy() == "minisql_v1"`:

- `load_entity(entity_id) -> dict[str, Any]`
- `save_entity(entity_id, fields: dict[str, Any]) -> None` — delegates to `upsert_entity_record`
- Keep `load()` / `save(full_data)` for bulk (used by migration, tests, analyze_storage)

### 3 — `SpecialistAgent.write_fields` / `read_fields`

- `write_fields`: if `minisql_v1`, use `load_entity` + mutate + `save_entity` (no full-document load/save).
- `read_fields`: if still loading full payload, switch to `load_entity` for minisql_v1.
- JSON strategy (`versioned_provenance_v1`): **unchanged** (still full document load/save).

### 4 — `write_bind_fields_multi` rollback (`src/agents/specialists/agent.py`)

Replace:

```python
snapshots[category] = copy.deepcopy(agent.storage.load())
```

With per-entity snapshot before write:

```python
snapshots[category] = agent.storage.load_entity(entity_id)  # or None if absent
```

On rollback, restore prior entity blob via `save_entity` or `delete_entity_record` if absent.

### 5 — Tests

Extend `tests/test_specialist_minisql_v1.py` (and/or new `tests/test_specialist_minisql_incremental.py`):

| Test | Assert |
|------|--------|
| Incremental write does not rewrite unrelated entities | Seed sqlite with entities A + B; `write_fields` on C only; A and B row counts + field JSON unchanged (read via sqlite3 or load_entity) |
| `write_fields` after migration uses O(1) entity path | Mock/spy or sqlite query log: incremental save does not execute `DELETE FROM field_records` without WHERE (or equivalent assertion) |
| Rollback on partial multi-category failure | Force failure on second category; first category entity restored to pre-write snapshot |
| Existing minisql_v1 tests | All prior tests still pass (bulk `save`/`load` roundtrip, migration backup, threshold migrate) |
| CRM smoke | `test_run_network_bootstrap_crm_seed` unchanged entity counts |

Optional micro-benchmark test (not gated on wall clock): N incremental writes to temp sqlite completes in reasonable bound vs full-replace regression — only if easy; otherwise document manual expectation in `output.md`.

### 6 — Docs

- **`docs/architecture.md`** — one paragraph: minisql_v1 specialist writes are per-entity upsert; bulk `save_payload` retained for migration.
- **`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`** — add **Test 6** row template (Paul + Grok fill `real` after fix); do not record numbers yourself.
- **Do not edit `TODO.md`.**

---

## Scope boundaries (strict)

**May modify:**

- `src/storage/minisql_v1.py`
- `src/agents/specialists/base.py`
- `src/agents/specialists/agent.py`
- `tests/test_specialist_minisql_v1.py` and/or `tests/test_specialist_minisql_incremental.py`
- `docs/architecture.md`
- `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` (test 6 template only)

**Do not modify:**

- `src/storage/entity_store.py`, `entity_registry.py` (alias index rebuild is follow-up)
- `examples/networks/baseball/*` (unless test requires — prefer framework tests)
- `admin-ui/`, `TODO.md`

---

## Explicit non-goals

- Incremental **entity registry** / `save_entities_document` full replace
- Skip index rebuild on `add_bind_alias` (separate slice)
- Changing versioned JSON specialist write path beyond unchanged behavior
- Bootstrap progress reporting (`2355` slice)
- Removing `load()` full payload for `analyze_storage` / admin diagnostics

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | `write_fields` on `minisql_v1` upserts single entity without table-wide DELETE |
| E2 | Unrelated entities unchanged after incremental write (test proves) |
| E3 | `write_bind_fields_multi` rollback uses per-entity snapshots |
| E4 | Migration + bulk `save_payload` still work |
| E5 | `./bin/ci-local` green |
| E6 | Paul can re-run timing test 6; expect **large** drop vs test 5 (hours → minutes target — Grok records actual) |

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, **"For Grok + Paul"**: queue timing test 6; note whether progress slice (`2355`) should run after this commit.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-17-2340-specialist-minisql-incremental-writes/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` and `next/`
4. **Do not commit or push** — tell Paul "slice ready for review"

**Suggested commit message:**

```
perf(specialist): incremental minisql_v1 per-entity upserts

Stop full-table DELETE/INSERT on each write_fields; load/save one
entity on minisql_v1 hot path. Per-entity rollback in
write_bind_fields_multi. Bulk save_payload retained for migration.
```

---

## For Grok + Paul

After approval: Paul re-runs baseball benchmark as **timing test 6** before or after progress slice; Grok reviews and records `real` in manual-check doc. Acknowledged miss: slice 2 review listed full replace as follow-up but did not block or queue before timing gates.
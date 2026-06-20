# Baseball bootstrap perf — deferred index rebuild + materialize player_debut

> **READY** — Profile-driven (Grok, 2026-06-20). **Do not edit `TODO.md`.**

## Objective

Cut Lahman cold bootstrap from **~26 min** to a demo-tolerable target (**~5–8 min** on Paul's machine) without a bulk SQL identity loader. Two changes backed by cProfile on `~/mycelium-networks/baseball`:

1. **Stop O(n²) field-index rebuilds** during deferred bootstrap.
2. **Materialize debut rows** at warehouse ingest so `distinct_player_debut_rows` drops from **~140 s** to sub-second.

## Background (profile summary)

| Phase | Current wall | Root cause |
|-------|--------------|------------|
| `distinct_player_debut_rows` | ~140 s | Heavy `People` ⋈ `Appearances` ⋈ `Teams` SQL every bootstrap |
| Player bind loop (~24k) | ~24 min | Each `save_entity` → `_rebuild_field_indexes()` scans all entities while `bootstrap_deferred_save()` is active |
| `ingest_warehouse` | ~2–7 s | Acceptable |

Bind-loop duplicate detection uses `bind_index` / `lookup_by_bind_values` — **not** field indexes mid-loop.

Reference: `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` (Test 9 baseline); `bin/profile-lahman-bootstrap`.

## Implementation

### 1 — Deferred bootstrap: one field-index rebuild

**File:** `src/agents/entity_registry.py`

When `_defer_flush()` is true, `_save()` must **not** call `_rebuild_field_indexes()` on every write. Keep a single rebuild in `commit_deferred_save()` (already calls `_rebuild_field_indexes()` before persist).

**Verify:** No bootstrap code path calls `lookup_by_field` / `intersect_lookup` mid-loop that requires a fresh index. Seed bind path uses `bind_index` only.

**Tests (framework, smoke):**

- Regression: existing entity-registry / bootstrap smoke tests green.
- New smoke test: under `bootstrap_deferred_save`, N sequential `save_entity` calls → `_rebuild_field_indexes` runs **once** at commit (mock/spy or call-count via test hook — smallest approach that proves the contract).

### 2 — Materialize `player_debut` at warehouse ingest

**File:** `examples/networks/baseball/bootstrap_handlers/lahman_common.py`

During `ingest_warehouse`, after CSV load, create and populate table `player_debut`:

- Columns: `playerID`, `display_name`, `debut_year`, `debut_team` (match current `distinct_player_debut_rows` output).
- Use the same SQL logic as today's `distinct_player_debut_rows` (one-time cost at ingest).

Change `distinct_player_debut_rows` to:

```sql
SELECT player_id, display_name, debut_year, debut_team FROM player_debut ORDER BY player_id
```

Add SQLite index on `player_debut(playerID)` if helpful.

**Tests (pack, smoke):**

- Minimal fixture bootstrap: `distinct_player_debut_rows` returns expected Aaron row.
- `tests/test_lahman_seed_handler.py` or existing baseball bootstrap smoke: assert `player_debut` row count > 0 after ingest.

### 3 — Optional (include if small)

Skip `ingest_warehouse` CSV wipe/reload when `warehouse/lahman.sqlite` exists and seed ref unchanged (mtime or `seed.source.json` version). Document behavior in `output.md`. Skip if it adds scope risk.

## Live gate

**N/A** — no user-visible query behavior change.

## Manual verification (required in `output.md`)

Ask Paul to re-run on full Lahman root:

```bash
time ./bin/refresh-example-network baseball --yes --no-default
```

Record **real/user/sys** and compare to Test 9 (~1579 s). Target: **< 600 s** cold bind (stretch); **< 480 s** would be excellent.

Also run warm handler profile:

```bash
MYCELIUM_BOOTSTRAP_PROGRESS=0 ./bin/profile-lahman-bootstrap ~/mycelium-networks/baseball
```

Expect `distinct_player_debut_rows` negligible and `build_field_indexes` ~1× at commit.

## Constraints

- **Clarity over cleverness** — no parallel bulk identity loader, no raw SQL bypass of `ensure_entity_bind_fields`.
- CRM / non-baseball networks unchanged unless framework fix in (1) is correctly generic.
- `./bin/ci-local` must pass.

## Output

Follow `prompts/cursor/WORKFLOW.md` completion checklist. Suggested commit message:

```
perf(baseball): bootstrap deferred index rebuild + player_debut table
```
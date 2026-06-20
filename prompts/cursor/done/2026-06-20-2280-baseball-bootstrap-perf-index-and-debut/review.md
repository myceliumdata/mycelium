# Review — baseball bootstrap perf (2280)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-21

## Context

Cursor slice from `prompts/cursor/next/2026-06-20-2280-baseball-bootstrap-perf-index-and-debut.md`. (1) Skip per-write `_rebuild_field_indexes()` during deferred bootstrap; one rebuild at `commit_deferred_save()`. (2) Materialize `player_debut` at warehouse ingest; `distinct_player_debut_rows` reads table. Full diff read before verdict.

**Show-stoppers for M14:** **None.** Performance targets are **Paul manual gate** — code contract is sound.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **640** smoke passed, ruff clean, admin-ui build ok |

## Delivery

`output.md` matches files on disk. Implementation complete.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Defer path skips field-index rebuild per `_save()` | Pass — `entity_registry.py` |
| `commit_deferred_save()` still rebuilds field indexes once | Pass — line 281 |
| Smoke: single `_rebuild_field_indexes` under defer | Pass — `test_bootstrap_deferred_save_single_field_index_rebuild` |
| Post-commit `lookup_by_field` works | Pass — asserted in same test |
| `player_debut` materialized at ingest | Pass — `_materialize_player_debut` after CSV load |
| `distinct_player_debut_rows` reads `player_debut` | Pass — same SQL logic as before (moved to ingest) |
| Minimal fixture Aaron debut row | Pass — `test_lahman_warehouse_materializes_player_debut` |
| Lahman bind path uses `bind_index` / `lookup_by_source_key` not `lookup_by_field` mid-loop | Pass — no field-index dependency during bind loop |
| Optional warehouse skip-on-unchanged | Deferred — documented in output |
| Live gate N/A | Pass |
| CRM generic framework fix | Pass — `save_entity` already passes `rebuild_source_key_index=False`; defer change is registry-wide but safe for CRM deferred bootstrap |

## Legacy / dual-path

- **Stale live warehouse** without `player_debut` table: `distinct_player_debut_rows` returns `[]` until full re-ingest — output documents; Paul must `--yes` refresh after merge.
- Non-deferred `_save()` unchanged (still rebuilds field indexes when not deferring).

## Tests

**Covered:** Framework defer contract (call count + lookup); pack `player_debut` row count + debut row equality.

**Gaps (non-blocking):**

- No test that materialize SQL matches pre-2280 output on multi-player fixture (only single Aaron row).
- Timing improvement not CI-verifiable — manual Test 10 required.

## Design critique

**Strong:** Minimal, high-leverage diff — 4-line framework change + ingest-time materialization. Preserves `ensure_entity_bind_fields` loop and uuid rules. `save_entity(..., rebuild_source_key_index=False)` means the O(n²) culprit was field indexes only; fix is correctly scoped. SQL extracted to `_PLAYER_DEBUT_MATERIALIZE_SQL` constant — single source of truth.

**Sub-optimal (non-blocking):**

- Defer path still **full** `_rebuild_source_key_index()` when callers pass `rebuild_source_key_index=True` — not hit by Lahman bind loop today; watch if future bootstrap paths regress.
- `player_debut` is pack-local, not in `BOOTSTRAP_TABLES` / manifest — fine for perf table; document that it's derived not Lahman CSV.
- `output.md` title says "M14" — wrong slice id (2280).

## Polish nits

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | `output.md` header says M14 | Fix typo in done artifact or ignore |
| N2 | Record Test 10 timing after Paul cold bootstrap | `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` |
| N3 | Optional ingest skip still open | Future slice if cold refresh still slow |

## Diff reviewed

- `src/agents/entity_registry.py`
- `examples/networks/baseball/bootstrap_handlers/lahman_common.py`
- `tests/test_entity_store_evolution.py`
- `tests/test_lahman_seed_handler.py`
- `prompts/cursor/done/2026-06-20-2280-baseball-bootstrap-perf-index-and-debut/` (`prompt.md`, `output.md`)

## For Paul

- **Required manual gate (timing):**
  ```bash
  time ./bin/refresh-example-network baseball --yes --no-default
  ```
  Record Test 10 in timing-gates doc; compare to Test 9 (~1579 s). Stretch target < 600 s.
- **Profile (optional):**
  ```bash
  MYCELIUM_BOOTSTRAP_PROGRESS=0 ./bin/profile-lahman-bootstrap ~/mycelium-networks/baseball
  ```
- **Live gate:** `./bin/gate-live baseball` after refresh (rebuilds `player_debut` + `Fielding`).
- **Next Cursor slice:** `2026-06-20-2340-baseball-warehouse-stat-specialist-base-class-m14.md` (framework warehouse bases).
- **Commit message:** `perf(baseball): bootstrap deferred index rebuild + player_debut table`
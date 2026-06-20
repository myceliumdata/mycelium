# Review — baseball full Lahman warehouse ingest (M13)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-21

## Context

Cursor slice from `prompts/cursor/next/2026-06-20-2260-baseball-full-warehouse-ingest-m13.md`. Expands `BOOTSTRAP_TABLES` to all **27** Lahman 2025 CSV tables; adds `BootstrapResult.warehouse_ingest_counts` for reporting; identity bind loop unchanged. Full diff read before verdict.

**Show-stoppers for 2280 / M14:** **None.**

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **638** smoke passed, ruff clean, admin-ui build ok |
| `uv run pytest tests/test_lahman_seed_handler.py -m smoke -q` | Included in ci-local — all pass |

## Delivery

`output.md` matches files on disk. Implementation complete.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| All 27 Lahman tables in `BOOTSTRAP_TABLES` | Pass — `LAHMAN_CSV_TABLE_COUNT = 27` |
| Row counts reported | Pass — `warehouse_ingest_counts` on `BootstrapResult` |
| uuid / registry stability | Pass — team + player bind logic untouched |
| `warehouse_manifest.json` | Pass — domain introspection unchanged (non-domain tables ingested only) |
| Minimal fixture smoke < seconds | Pass — full-fixture test with 1-row stubs per table |
| Live gate new scenarios | N/A — per prompt |
| `TODO.md` untouched | Pass |
| CRM bootstrap unchanged | Pass — optional field on `BootstrapResult` only |

## Legacy / dual-path

- Existing `seed_fixture="minimal"` tests unchanged (subset CSVs; ingest skips missing files).
- `DefaultSeedHandler` / CRM `BootstrapResult` callers unaffected — new field defaults to `{}`.
- `ingest_warehouse` still rebuilds sqlite from scratch each bootstrap (delete + reload).

## Tests

**Covered:** New `test_lahman_seed_handler_ingests_all_lahman_tables` — 27 tables, counts > 0, sqlite row counts match, manifest file exists.

**Gaps (non-blocking):**

- Test hardcodes `27` instead of importing `LAHMAN_CSV_TABLE_COUNT` from `lahman_common`.
- No assertion that `warehouse_ingest_counts` surfaces in bootstrap CLI/report output (field exists but may not be printed yet).
- `docs/seed-bootstrap.md` not updated with `warehouse_ingest_counts` field.

## Design critique

**Strong:** Minimal, correct expansion — one tuple change + reporting hook. Separating **warehouse bulk load** from **identity bind** keeps M13 orthogonal to 2280 perf work. Full-table fixture dictionary is thorough and makes the 27-table contract explicit.

**Sub-optimal (non-blocking):**

- `_FULL_LAHMAN_FIXTURE_CSV` duplicates overlap with `_write_minimal_lahman_fixture` (maintenance burden if schemas drift).
- Prompt mentioned manifest “as needed”; non-domain tables (awards, postseason, …) are in sqlite but not `warehouse_domains.json` — correct for current factory model, worth one sentence in program doc when Paul updates slice map.

## Polish nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | Test magic number `27` | Import `LAHMAN_CSV_TABLE_COUNT` — `2350` or doc polish |
| N2 | `seed-bootstrap.md` omits `warehouse_ingest_counts` | Doc sync in `2350` |
| N3 | Bootstrap CLI may not print ingest counts | Wire to progress/report if Paul wants test 6 visibility — optional with 2280 |

Folded into `2350` where noted.

## Diff reviewed

- `examples/networks/baseball/bootstrap_handlers/lahman_common.py`
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`
- `src/network/bootstrap/context.py`
- `tests/test_lahman_seed_handler.py`
- `prompts/cursor/done/2026-06-20-2260-baseball-full-warehouse-ingest-m13/` (`prompt.md`, `output.md`)

## For Paul

- **Operator (required after merge):**
  ```bash
  ./bin/refresh-example-network baseball --sync-only   # or --yes for full re-bootstrap
  ./bin/gate-live baseball
  ```
  Update anchors + drift only if reload changes stat values — do not weaken assertions silently.
- **Timing:** Re-run **test 6** on full Lahman zip (`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`). Expect warehouse ingest wall-clock to rise (~700k rows); identity bind loop unchanged (2280 target).
- **Next Cursor slice:** `2026-06-20-2280-baseball-bootstrap-perf-index-and-debut.md` — review alone when done.
- **Commit message:** `baseball: ingest all 27 Lahman CSV tables in warehouse bootstrap (M13)`
# Baseball full Lahman warehouse ingest (M13) — output

## Summary

Extended `BOOTSTRAP_TABLES` in `lahman_common.py` from 8 tables to **all 27 Lahman 2025 CSV tables** (per `readme2025.txt`). Warehouse ingest still skips missing CSV files; identity bind logic unchanged (team + player only). Row counts are returned on `BootstrapResult.warehouse_ingest_counts` for bootstrap reporting.

## Design (v1 — locked)

| Decision | Choice |
|----------|--------|
| Table list | Explicit 27-name tuple aligned with `lahman_1871-2025_csv/*.csv` |
| Registry | No change — uuid stability on player/team binds preserved |
| Manifest | `maybe_write_warehouse_manifest` unchanged; introspects domain tables only |
| Reporting | New optional `BootstrapResult.warehouse_ingest_counts: dict[str, int]` |

## Files

| Area | Files |
|------|--------|
| Ingest | `examples/networks/baseball/bootstrap_handlers/lahman_common.py` — full `BOOTSTRAP_TABLES`, `LAHMAN_CSV_TABLE_COUNT` |
| Handler | `lahman_seed.py` — sets `warehouse_ingest_counts` on result |
| Framework | `src/network/bootstrap/context.py` — `warehouse_ingest_counts` field |
| Tests | `tests/test_lahman_seed_handler.py` — 27-table minimal fixture + ingest assertion |

## Verification

```text
./bin/ci-local                              # 638 smoke passed
uv run pytest tests/test_lahman_seed_handler.py -m smoke -q
```

Full-fixture bootstrap completes in **<1 s** on minimal CSV stubs.

## For Grok + Paul

- Mark M13 full warehouse ingest shipped in program slice map.
- **Paul — after merge:** re-run timing **test 6** on full Lahman zip (`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`). Warehouse ingest adds ~19 tables (~700k rows total); expect modest wall-clock increase on warehouse phase only — identity bind loop unchanged.
- **Paul — live root:** run `./bin/refresh-example-network baseball --sync-only` (or `--yes` for full re-bootstrap), then `./bin/gate-live baseball`. If anchors drift after reload, update `baseball_aaron_lahman_v2025.json` + `gate_runner.py` — do not weaken assertions without documenting why.
- Live gate: **N/A new scenarios** — existing 26 baseball scenarios should pass after reload.

## Suggested commit message

```
baseball: ingest all 27 Lahman CSV tables in warehouse bootstrap (M13)
```

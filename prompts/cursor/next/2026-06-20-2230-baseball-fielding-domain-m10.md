# Baseball fielding domain (M10)

> **READY** — Thin wrapper on `pack_common` (same as `pitching_specialist.py`). **Do not edit `TODO.md`.**

## Objective

Add **fielding** category to committed ontology + `fielding_specialist.py` pack module + `warehouse_domains.json` domain on `Fielding` table.

## Pack pattern (mandatory)

- **`fielding_specialist.py`** is a thin wrapper only: copy the `pack_bootstrap` block from `pitching_specialist.py`, then delegate to `pack_common.run_warehouse_player_graph(..., category="fielding", domain="fielding")`.
- **Do not** duplicate graph helpers, field evaluation loops, or response assembly — that lives in `pack_common.py`.
- Extend `warehouse_resolve.py` / manifest only; no new graph logic unless `pack_common` truly needs a shared hook (unlikely for v1 `career_sum` aliases).

## v1 attributes

- `career_games` → `career_sum` on `G`
- `career_putouts` → `career_sum` on `PO` (verify Lahman column name in schema pass)

## Bootstrap

- Add `Fielding` to `BOOTSTRAP_TABLES` in `lahman_common.py` (if not already — M12 may subsume; at minimum ingest for tests).

## Tests

- Minimal fixture Fielding.csv for sample player.
- `tests/test_baseball_fielding_specialist.py` smoke.
- Add to `bin/smoke-baseball-e2e` pytest list.

## Live gate (required)

Add **`bb-field-01`** to `tests/live/catalogs/baseball.yaml` (new phase `fielding` — add to `tests/live/networks.yaml` `baseball.phases`):

- Player with known fielding totals on full Lahman (e.g. Ozzie Smith or Aaron if non-zero on root) — `career_games` + `career_putouts` two-step deliver.
- New anchors in `baseball_aaron_lahman_v2025.json` (e.g. `fielder_player`, `fielder_career_games`) from live root discovery.
- `gate_runner.py` drift checks for fielding attrs.

`@pytest.mark.live_gate` only — never default CI.
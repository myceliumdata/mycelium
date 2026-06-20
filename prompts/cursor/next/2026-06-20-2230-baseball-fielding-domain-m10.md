# Baseball fielding domain (M10)

> **READY** — Clone M5 pitching pattern. **Do not edit `TODO.md`.**

## Objective

Add **fielding** category to committed ontology + `fielding_specialist.py` pack module + `warehouse_domains.json` domain on `Fielding` table.

## v1 attributes

- `career_games` → `career_sum` on `G`
- `career_putouts` → `career_sum` on `PO` (verify Lahman column name in schema pass)

## Bootstrap

- Add `Fielding` to `BOOTSTRAP_TABLES` in `lahman_common.py` (if not already — M12 may subsume; at minimum ingest for tests).

## Tests

- Minimal fixture Fielding.csv for sample player.
- `tests/test_baseball_fielding_specialist.py` smoke.
- Add to `bin/smoke-baseball-e2e` pytest list.
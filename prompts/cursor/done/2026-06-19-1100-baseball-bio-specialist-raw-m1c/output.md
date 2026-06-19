# Output — baseball bio specialist raw read (M1c)

## Summary

Raw Lahman `People` read for `birth_date` via `bio_specialist`: fixture Hank Aaron → `1934-02-05` with computation-centric provenance (dataset pin + `computation.inline` + `parameters`). Reuses M1b framework unchanged.

## Changes

| Area | Change |
|------|--------|
| `examples/networks/baseball/specialists/bio_specialist.py` | Warehouse `People` birth columns → `YYYY-MM-DD`; cache + `write_computed_field` |
| Minimal Lahman fixtures | `People.csv` adds `birthYear`, `birthMonth`, `birthDay` for `aaronha01` |
| `tests/test_baseball_bio_specialist.py` | Deliver, provenance, cache, missing birthMonth → `na` |
| `bin/smoke-baseball-e2e` | `birth_date` scenario (8 scenarios total); M1b `career_hr` unchanged |
| `examples/networks/baseball/README.md` + `queries/04-birth-date.json` | Step-1/2 example |

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **564** smoke passed |
| `./bin/smoke-baseball-e2e` | **8** scenarios passed |

## For Grok + Paul

- Mark **M1c** done in `TODO.md` when approved.
- **Hand-test order:** `birth_date` (raw) on full Lahman, then `career_hr` (aggregate).
- Live root: `./bin/refresh-example-network baseball --sync-only`.
- **Next in queue:** `2026-06-19-1200-baseball-m1b-polish-nits.md` (M1b review nits).
- No commit (per workflow).

**Suggested commit message:**

```
baseball: bio specialist birth_date raw read + provenance (M1c)
```

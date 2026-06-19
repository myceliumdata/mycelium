# Review — baseball bio specialist raw read (M1c)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## Scope checked

Full read of M1c deliverables against prompt and [`2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md):

| Area | Assessment |
|------|------------|
| `bio_specialist.py` | Mirrors `batting_specialist.py`; pack-only Lahman SQL; `write_computed_field` + dataset pin |
| Fixture builders | `People.csv` birth columns added in all five minimal-fixture helpers |
| `tests/test_baseball_bio_specialist.py` | Deliver, provenance shape, cache, missing `birthMonth` → na |
| Smoke | 8 scenarios; `birth_date_routes_bio_specialist` asserts routing, value, provenance |
| Docs | README + `queries/04-birth-date.json` |
| M1b regression | `career_hr==3` scenario unchanged; batting tests still in CI set |

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **564** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` (clean env) | **8** scenarios passed |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Raw `People` read → `1934-02-05` | Pass |
| Provenance: dataset + `computation.inline` + `parameters` | Pass |
| No web research / aggregates | Pass |
| Reuse M1b framework unchanged | Pass |
| Pack install via `specialists/*.py` copy (M1b) | Pass (implicit via refresh tests) |
| Other bio attrs → `na` | Pass |
| Missing birth parts → `na` | Pass |

## Design critique

**Strong:** Clean mirror of M1b pack pattern; correct progression (raw before aggregates); provenance envelope matches locked design; tests and smoke cover the full step-1/2 deliver path.

**Sub-optimal (non-blocking):** Same structural nits as M1b — inline provenance string drifts from executed `query_warehouse` SQL; `_mark_na` uses full storage load/save; `pending` list is never populated so overall-status branch is dead code. Queued polish slice `2026-06-19-1200` already targets batting + bio for P1–P2.

## Polish nits (non-blocking)

| # | Nit | Note |
|---|-----|------|
| P1 | `BIRTH_DATE_COMPUTATION_INLINE` vs `_compute_birth_date` SQL (quotes, `query_warehouse`) | Same drift pattern as M1b P1; fold into `1200` polish slice. |
| P2 | `_mark_na` full `storage.load()` / `save()` | Same as M1b P2; `1200` slice covers `bio_specialist.py`. |
| P3 | `pending` never appended; unreachable status branches | Harmless; simplify in `1200` when touching both specialists. |
| P4 | `test_birth_date_missing_birth_month_na` accepts `"pending"` | Looser than ideal; tighten to `N/A` once status logic is cleaned. |

## Diff reviewed

- `examples/networks/baseball/specialists/bio_specialist.py` (new)
- `tests/test_baseball_bio_specialist.py` (new)
- `examples/networks/baseball/queries/04-birth-date.json` (new)
- `bin/smoke-baseball-e2e`
- `examples/networks/baseball/README.md`
- `tests/test_baseball_batting_specialist.py`
- `tests/test_baseball_pack_ontology.py`
- `tests/test_lahman_seed_handler.py`
- `tests/test_example_network.py`
- `prompts/cursor/done/2026-06-19-1100-baseball-bio-specialist-raw-m1c/` (`prompt.md`, `output.md`)

## For Paul

- **Commit message:** `baseball: bio specialist birth_date raw read + provenance (M1c)`
- **Hand-test order:** `birth_date` on full Lahman (`./bin/refresh-example-network baseball --sync-only`), then `career_hr`.
- **Next in queue:** `2026-06-19-1200-baseball-m1b-polish-nits.md` (P1–P3 for batting + bio).
- **Push:** local only until program gate; no `origin` push unless you ask.
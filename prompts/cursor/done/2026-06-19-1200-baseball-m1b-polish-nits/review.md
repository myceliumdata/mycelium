# Review — baseball M1b polish nits (slice 1200)

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## Scope checked

Full read of slice deliverables against prompt and M1b/M1c review nits P1–P3:

| Area | Assessment |
|------|------------|
| **P1** batting | `career_hr()` is compute + provenance source; `inspect.getsource(career_hr)` — zero drift |
| **P1** bio (bonus) | Same pattern for `birth_date()` — aligned with M1c nit backlog |
| **P2** | `SpecialistAgent.write_na_field()` mirrors `write_computed_field` incremental branch; pack specialists call it |
| **P3** | `_overall_field_status()` replaces dead branching in batting + bio |
| Framework | Minimal `write_na_field` on `SpecialistAgent` — justified per prompt |
| Tests | Inline `SUM`/`playerID` assertion; minisql `write_na_field` incremental test |

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **565** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` (clean env) | **8** scenarios passed |
| `tests/test_baseball_batting_specialist.py` + `test_baseball_bio_specialist.py` | **8** passed |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| P1 — provenance inline matches executed code | Pass |
| P2 — `_mark_na` incremental on minisql_v1 | Pass |
| P3 — status branching simplified, outcomes unchanged | Pass |
| Behavior unchanged (`career_hr==3`, provenance keys) | Pass |
| No new attrs / schema changes | Pass |
| CRM / factory untouched | Pass |

## Design critique

**Strong:** P1 fix is the right approach (`inspect.getsource` on the function actually called). `write_na_field` cleanly deduplicates incremental logic for pack specialists. Bio got the same polish without scope creep beyond P2’s explicit call-out.

**Minor (non-blocking):** Bio provenance test does not assert `birthYear` in inline (batting test covers P1 pattern). M1c P4 (tighten missing-month test to `N/A` only) still open — status helper is cleaner but test assertion unchanged.

## Diff reviewed

- `examples/networks/baseball/specialists/batting_specialist.py`
- `examples/networks/baseball/specialists/bio_specialist.py`
- `src/agents/specialists/agent.py` (`write_na_field`)
- `tests/test_baseball_batting_specialist.py`
- `tests/test_specialist_minisql_incremental.py`
- `prompts/cursor/done/2026-06-19-1200-baseball-m1b-polish-nits/` (`prompt.md`, `output.md`)

## For Paul

- **Commit message:** `polish(baseball): align batting specialist provenance and storage paths (M1b nits)`
- **Hand-test gate** (unchanged behavior — ~10 min sanity):
  1. `./bin/refresh-example-network baseball --sync-only`
  2. `birth_date` + `career_hr` on Hank Aaron with `provenance: true`
  3. Skim `computation.inline` — should match `career_hr()` / `birth_date()` source (with `query_warehouse`)
  4. Repeat step 2 to confirm cache
- **Push:** local only until program gate.
# Review — baseball roster product specialist (M11)

**Verdict:** **Approved + polish nits** (batch M10–M12)  
**Reviewer:** Grok  
**Date:** 2026-06-21

## Context

`roster_specialist` + shared `product_common.run_product_team_specialist`; scoped `Appearances` ⋈ `People`; attr `roster` as JSON name array; live gate `bb-roster-01` with `contains` assertion.

**Show-stoppers:** None for M13 / 2280. **Important non-blocking:** scope-aware cache (see N1).

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **637** smoke passed |
| Roster smokes | **2** passed (scoped deliver + no-scope → N/A) |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Product specialist (not manifest wrapper) | Pass — `product_common.py` |
| `scope.yearID` required for roster | Pass — documented in output; `test_roster_without_scope_is_na` |
| Provenance `lahman.teamID`, `yearID`, inline | Pass |
| `bb-roster-01` + `contains` operator | Pass — new `assertions.py` `contains` |
| Drift check in `gate_runner.py` | Pass |
| Single specialist deliver (not fan-out) | Pass |

**Spec gap (non-blocking):** Prompt design lock promised cache key `(teamID, yearID)`; storage cache is per-entity field `roster` only — second scoped year can return stale roster until cache cleared.

## Design critique

**Strong:** `product_common` is the right shared shell for roster + franchise; `compute_attr` callback keeps specialists thin. `contains` gate assertion is pragmatic for variable-length rosters. No-scope → `N/A` is explicit and tested.

**Sub-optimal:** Product graph loop duplicates `pack_common` response assembly (~80 lines) — candidate for `ProductTeamSpecialist` base class (parallel to M14 warehouse base class, not in M14 scope).

## Polish nits

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | Roster cache ignores `yearID` — violates design-lock cache key | Scope-aware storage key or invalidate on scope mismatch — `2350` or small fix before public demo |
| N2 | No test for 1957 then 1958 roster on same team entity | Add after N1 fix |
| N3 | `roster_count_1957_bro` anchor unused in catalog (doc-only) | Use in drift or remove from anchors |

## Diff reviewed

- `roster_specialist.py`, `product_common.py`, `categories.json`
- `tests/test_baseball_roster_specialist.py`
- `tests/live/assertions.py`, catalog, `gate_runner.py`
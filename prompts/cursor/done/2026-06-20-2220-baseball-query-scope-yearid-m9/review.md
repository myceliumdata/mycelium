# Review — baseball query scope yearID (M9)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-20

## Context

Cursor slice from `prompts/cursor/next/2026-06-20-2220-baseball-query-scope-yearid-m9.md`. Framework + pack: optional `EntityQuery.scope.yearID` bound on delivery, replayed on step 2, wired through `pack_common` / `warehouse_resolve` for `team_latest_column`; `career_sum` ignores scope. Full diff read before verdict.

**Show-stoppers for M10–M12:** **None.** M11 roster and M12 franchise can rely on `scope.yearID` as documented; framework delivery replay is correct.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **632** smoke passed, ruff clean, admin-ui build ok |

## Delivery

`output.md` matches files on disk. Implementation complete.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Top-level `EntityQuery.scope` (not under `lookup`) | Pass — documented in `docs/query-record-type-router.md` |
| Step 2 forbids `scope` on public query | Pass — validator + `test_scope_rejected_on_step2` |
| Scope bound on `DeliveryScope.query_scope` at issue | Pass — `target_resolve.issue_target_delivery` |
| Step 2 replays scope via graph state | Pass — `dispatch.py` → `delivery_scope_query_scope` |
| `team_season`: scoped `season_wins` / `season_losses` | Pass — `team_latest_column` + smoke + `bb-team-02` |
| Unscoped team reads → latest year (M6 default) | Pass — existing `test_season_wins_latest_year` unchanged |
| `career_sum` ignores `yearID` | Pass — resolver unchanged; `test_career_hr_ignores_year_scope` + `bb-scope-01` |
| Provenance `parameters.yearID` when scope applies | Pass — team scoped test asserts `yearID: "1957"` |
| Scope logic in `warehouse_resolve` / `pack_common`, not specialist files | Pass — thin wrappers untouched |
| Live gate `bb-team-02` + optional `bb-scope-01` | Pass — both in catalog |
| `bb-team-01` unchanged | Pass — catalog retained |
| Backward compatible / CRM unchanged | Pass — optional field, default `{}` |
| `TODO.md` untouched | Pass |

**Deferred by design (documented in output):** `season_column` convention shipped in resolver but no manifest aliases yet — batting/pitching per-season attrs wait for a future slice (M10+ fielding or explicit season attrs). Prompt behavior bullet overstated; output correctly locks v1.

## Legacy / dual-path

- Omitting `scope` preserves prior latest-year team reads and career totals.
- Existing deliveries without `query_scope` deserialize as `{}` via `default_factory`.
- `issue_delivery(..., query_scope=None)` remains backward compatible for CRM and unit tests.

## Tests

**Covered:**

- Delivery persistence: `test_issue_delivery_persists_query_scope`
- Step-2 rejection: `test_scope_rejected_on_step2`
- Team scoped deliver + provenance `yearID`
- Career total with bogus scope
- Live gate catalog count ≥ 23

**Gaps (non-blocking):**

- No test that `career_hr` provenance **omits** `yearID` when scope present (today `provenance_parameters` always forwards `year_id` even for `career_sum` — misleading metadata).
- No gate scenario for invalid/missing `yearID` on team scope (wrong year → `N/A` or empty) — operator hand-test only.
- `test_issue_delivery_roundtrip` no longer asserts `deliveries.json` exists (assert moved to sibling test).

## Design critique

**Strong:** Clean split — framework owns `EntityQuery.scope`, `DeliveryScope.query_scope`, and step-2 hydration; pack owns `query_year_id()` and SQL conventions. `team_latest_column` extension is minimal and correct. `season_column` hook is forward-looking without premature manifest entries. Router doc § Query scope (M9) is the right place for the contract.

**Sub-optimal (non-blocking):**

- `year_id` passed into `provenance_parameters` / `team_provenance_parameters` for **all** resolves, including `career_sum` where scope is intentionally ignored — provenance can imply season filtering on career totals.
- `EntityQuery.scope: dict[str, str]` does not coerce numeric `yearID` at the model layer (normalization only at `issue_delivery`); inconsistent if a client bypasses issue path.
- v1 scope is `yearID` only; prompt title mentions `teamID` but output locks year-only — fine for roster (M11 uses team entity + year scope).

## Polish nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | `career_sum` provenance includes `parameters.yearID` when scope set but computation ignores it | Only attach `yearID` to provenance for conventions that consume scope (`team_latest_column`, `season_column`) — `2350` polish |
| N2 | No provenance assert on `test_career_hr_ignores_year_scope` | Assert `yearID` absent (after N1 fix) or document intentional omission |
| N3 | Trailing newline missing on `test_baseball_team_season_specialist.py` | Trivial format — `2350` |
| N4 | `test_issue_delivery_roundtrip` lost file-exists assert | Restore in roundtrip or shared helper — `2350` |
| N5 | No smoke for team scope with unknown `yearID` → `N/A` | Optional edge-case test — `2350` or M11 if roster hits same SQL path |

Folded into `prompts/cursor/next/2026-06-20-2350-baseball-program-polish-capstone.md` § M9.

## Diff reviewed

- `src/models/state.py` — `EntityQuery.scope`, `delivery_scope_query_scope`, step-2 validator
- `src/network/delivery.py` — `DeliveryScope.query_scope`, `issue_delivery` kwarg
- `src/agents/target_resolve.py` — bind scope at issue
- `src/agents/dispatch.py` — hydrate scope on step-2 deliver
- `examples/networks/baseball/specialists/pack_common.py` — `query_year_id`, pass-through
- `examples/networks/baseball/specialists/warehouse_resolve.py` — `team_latest_column` scope, `season_column`, provenance `yearID`
- `examples/networks/baseball/warehouse_domains.json` — convention note
- `docs/query-record-type-router.md` — § Query scope (M9)
- `docs/manual-checks/2026-06-20-live-gate-program.md` — count 23
- `tests/live/catalogs/baseball.yaml` — `bb-team-02`, `bb-scope-01`
- `tests/test_baseball_team_season_specialist.py`
- `tests/test_baseball_batting_specialist.py`
- `tests/test_delivery_store.py`
- `tests/test_target_step1_lookup_clarity.py`
- `tests/test_live_gate_runner_unit.py`
- `prompts/cursor/done/2026-06-20-2220-baseball-query-scope-yearid-m9/` (`prompt.md`, `output.md`)

## For Paul

- **Verdict:** Safe to batch **M10 → M11 → M12** in one Cursor session. No M9 fix slice required.
- **Operator:** `./bin/refresh-example-network baseball --sync-only` then `./bin/gate-live baseball --phase team_season` (and full gate when convenient).
- **Commit message:** `baseball: query scope yearID for season warehouse reads (M9)`
- **Next:** `2026-06-20-2230-baseball-fielding-domain-m10.md` (batch through M12 if desired).
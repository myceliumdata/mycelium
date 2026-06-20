# Baseball query scope — yearID (M9) — output

## Summary

Shipped optional **`scope: {yearID: "…"}`** on step-1 `EntityQuery`, persisted on `DeliveryScope.query_scope` and replayed on step 2 via `delivery_scope_query_scope`. Team season reads use scoped year when present; `career_sum` / `career_era_weighted` ignore scope. Provenance `parameters.yearID` set when scope applies.

## Design (v1 — locked in output)

| Decision | Choice |
|----------|--------|
| Scope shape | Top-level `EntityQuery.scope: dict[str, str]` (not nested under `lookup`) |
| Step 2 | Scope forbidden on public query; bound on delivery at issue time |
| Team reads | `team_latest_column` uses scoped `yearID` or latest year when omitted |
| Career totals | `career_sum`, `career_era_weighted` ignore `yearID` |
| Future season pulls | `season_column` convention added (requires `yearID`; not wired in manifest yet) |

Documented in `docs/query-record-type-router.md` § Query scope (M9).

## Files

| Area | Files |
|------|--------|
| Framework | `src/models/state.py` — `EntityQuery.scope`, `delivery_scope_query_scope` |
| Delivery | `src/network/delivery.py` — `DeliveryScope.query_scope` |
| Target | `src/agents/target_resolve.py`, `src/agents/dispatch.py` — bind + hydrate scope |
| Resolver | `warehouse_resolve.py` — scoped `team_latest_column`, `season_column`, provenance `yearID` |
| Pack | `pack_common.py` — `query_year_id()`, pass through evaluate helpers |
| Manifest | `warehouse_domains.json` — convention note update |
| Tests | `test_baseball_team_season_specialist.py`, `test_baseball_batting_specialist.py`, `test_delivery_store.py`, `test_target_step1_lookup_clarity.py` |
| Live gate | `bb-team-02`, `bb-scope-01` in `baseball.yaml` |

## Verification

```text
./bin/ci-local                              # 632 smoke passed
uv run pytest tests/test_baseball_team_season_specialist.py tests/test_baseball_batting_specialist.py -m smoke -q
uv run pytest tests/test_live_gate_runner_unit.py -q
```

Baseball catalog: **23** scenarios.

## For Grok + Paul

- Mark M9 query scope shipped in program slice map.
- Next queued slice: `2026-06-20-2230-baseball-fielding-domain-m10.md`.
- Operator: scoped team gate `./bin/gate-live baseball --phase team_season`.

## Suggested commit message

```
baseball: query scope yearID for season warehouse reads (M9)
```

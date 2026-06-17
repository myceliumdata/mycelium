# Output — strict lookup-key grain routing

## Summary

**Breaking** baseball identity refactor: removed multi-grain fan-out, grain-disambiguation LLM, and `EntityQuery.grain`. Step-1 routing uses `infer_grain_from_lookup()` — lookup key set must **exactly match** one grain's `bind_fields`.

Baseball manifest bind fields renamed: `team` grain `["team"]`, player grain `["player", "team"]` (was `name` / `name+team`).

## Changes

| Area | Change |
|------|--------|
| `network/mvr.py` | `infer_grain_from_lookup()`, `GrainInferenceResult` |
| `target_resolve.py` | Multi-grain path → inference + single-grain resolve; `resolve_id_all_grains` inlined |
| **Deleted** | `query_grain_router.py`, `grain_disambiguation.py`, `tests/test_query_grain_router.py` |
| `models/state.py` | Removed `EntityQuery.grain` |
| Baseball manifest + `lahman_seed.py` | `player` / `team` bind keys |
| `tests/test_strict_grain_routing.py` | **New** — 10 scenarios (no `grain=` on queries) |
| Tests/docs/scripts | Updated closed-identity, lahman, entity store, mvr resolve, smoke-baseball-e2e, ship gate |
| `bin/baseball-query` | Committed helper with new lookup keys |
| `docs/query-grain-router.md` | Replaced fan-out doc with lookup-key routing table |

## Routing contract (baseball)

| Lookup keys | Grain |
|-------------|-------|
| `{player, team}` | `player` |
| `{team}` | `team` |
| `{player}` | `lookup_incomplete` (needs `team`) |

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **500** smoke passed |
| `bin/smoke-baseball-e2e` | **6/6** scenarios |

## Paul manual gate (required after merge)

**Re-bootstrap** — existing benchmark entity stores use old `name` bind keys.

```bash
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root /tmp/mycelium-baseball-benchmark --yes --no-default
```

Then ship gate Checks 4–5 with new keys:

```bash
export ROOT=/tmp/mycelium-baseball-benchmark
export MYCELIUM_NETWORK_ROOT="$ROOT"
./bin/baseball-query '{"lookup": {"player": "Hank Aaron", "team": "Milwaukee Braves"}}'
./bin/baseball-query '{"lookup": {"team": "Brooklyn Dodgers"}}'
```

## For Grok + Paul

- **Breaking change** — Paul must re-bootstrap before ship gate.
- **Problem 2 deferred items** addressed for routing; suggestion flood / field_alias pollution remain out of scope if still observed.
- Update `HOLD.md` / `TODO.md` (Paul owns `TODO.md`).
- No commit (per workflow).

**Suggested commit message:**

```
refactor(routing): strict lookup-key grain inference; remove fan-out and EntityQuery.grain
```

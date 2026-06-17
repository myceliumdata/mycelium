# Output — bind-index fallback for step-1 full MVR lookup

## Summary

Multi-team players bootstrap alternate `(name, team)` tuples via `add_bind_alias` → `bind_index` only. Step-1 resolve used field-index AND exclusively, so alias binds missed. `lookup_by_target_lookup` now falls back to `lookup_by_bind_values` on empty field-index hits when the lookup is a full MVR for the grain.

**Problem 2 deferred:** multi-grain fan-out when player misses and team wins; `same_bind_field_conflict` suggestion flood; polluted `field_aliases` from lazy LLM expansion — out of scope.

## Changes

| File | Change |
|------|--------|
| `src/agents/entity_registry.py` | `lookup_by_target_lookup` bind_index fallback + docstring |
| `tests/test_entity_store_evolution.py` | `test_lookup_by_target_lookup_bind_index_fallback_for_alias_bind` |
| `tests/test_lahman_seed_handler.py` | Multi-team test asserts `lookup_by_target_lookup` for both teams |
| `tests/test_mvr_target_resolve.py` | `test_baseball_player_alias_bind_step1_lookup_resolved` (graph step-1) |
| `docs/seed-bootstrap.md` | Bind alias table note for step-1 fallback |
| `docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md` | Check 4: Milwaukee Braves alias command after slice 1000 |

## Behavior (locked)

| Lookup | Result |
|--------|--------|
| Full MVR, primary bind (field index hit) | `[entity.id]` via field index |
| Full MVR, alias bind (field index miss, bind_index hit) | `[entity.id]` via bind_index fallback |
| Partial lookup (e.g. `team` only) | Field-index only; no bind_index fallback |

## Exit criteria

| # | Status |
|---|--------|
| Registry fallback | Implemented |
| Unit + Lahman + graph tests | 3 new smoke tests |
| Docs | seed-bootstrap + ship gate Check 4 |
| `./bin/ci-local` | **502** smoke passed |

## Manual verification (Paul/Grok post-merge)

No data reload required — existing benchmark roots have correct `bind_index` keys.

```bash
export ROOT=/tmp/mycelium-baseball-benchmark
export MYCELIUM_NETWORK_ROOT="$ROOT"
./bin/baseball-query '{"lookup": {"name": "Hank Aaron", "team": "Milwaukee Braves"}, "grain": "player"}'
# Expect: lookup_resolved, total_matches: 1
```

## For Grok + Paul

- Ship gate **Check 4** should pass for non-primary Aaron teams after merge (e.g. Milwaukee Braves).
- **Problem 2** (multi-grain / suggestions / field_alias pollution) remains a separate slice.
- No commit (per workflow).

**Suggested commit message:**

```
fix(registry): step-1 full MVR lookup falls back to bind_index for alias binds
```

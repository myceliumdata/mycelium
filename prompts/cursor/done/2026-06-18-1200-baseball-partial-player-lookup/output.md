# Output — baseball partial player lookup (CRM parity)

## Summary

Multi-grain step-1 no longer returns `lookup_incomplete` immediately when `infer_grain_from_lookup` identifies an unambiguous partial subset. Instead, `resolve_target_step1` delegates to `_resolve_single_grain_step1` on `inference.grain` — same path CRM single-grain networks already use.

`{player}`-only baseball lookups now hit the field index first: unique names resolve, homonyms multi-match, unknown names still ask for `team`.

## Changes

| Area | Change |
|------|--------|
| `src/agents/target_resolve.py` | On `lookup_incomplete` + `inference.grain`, delegate to `_resolve_single_grain_step1` |
| `tests/test_strict_grain_routing.py` | Renamed incomplete test to unknown name; added unique-resolve + homonym tests |
| `docs/query-grain-router.md` | `{player}` only row + framework step 4 delegation note |
| `docs/manual-checks/2026-06-18-baseball-query-hand-test-plan.md` | Q05 → unknown name; new Q17 known unique; matrix G |
| `examples/networks/baseball/guide.md` | Partial `{player}` sentence |

`infer_grain_from_lookup` unchanged.

## Routing contract (baseball) — updated row

| Lookup keys | Grain | Step-1 (typical) |
|-------------|-------|------------------|
| `{player}` only | `player` (partial) | Field index → resolved / multi-match / incomplete |

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **502** smoke passed |
| `./bin/smoke-baseball-e2e` | **6/6** |
| `./bin/smoke-crm-e2e` | **7/7** |

## Paul manual gate (no re-bootstrap)

Existing post-1100 benchmark root is fine. Hand tests:

```bash
export ROOT="${ROOT:-/tmp/mycelium-baseball-benchmark}"
export MYCELIUM_NETWORK_ROOT="$ROOT"
./bin/baseball-query '{"lookup": {"player": "Hank Aaron"}}'   # → lookup_resolved
./bin/baseball-query '{"lookup": {"player": "Nobody Here"}}'  # → lookup_incomplete, team required
```

## For Grok + Paul

- **Router contract change:** `{player}` only is no longer immediate `lookup_incomplete`; see `docs/query-grain-router.md`.
- **Hand test plan:** Q05 = unknown name incomplete; **Q17** = known unique resolves (e.g. Hank Aaron).
- **HOLD.md:** Mark 1200 done; remove from pending queue.
- **No re-bootstrap** unless root still has pre-1100 `{name, team}` keys.
- No commit (per workflow).

**Suggested commit message:**

```
fix: delegate partial multi-grain lookups to single-grain resolver (CRM parity)

{player}-only baseball lookups now hit the field index before
lookup_incomplete, matching CRM partial name behavior.
```

# Output — baseball MVR record_type + debut bind

## Summary

**Breaking** vocabulary and baseball player bind refactor:

- `mvr.grains` → `mvr.record_types`; `identity_mode` → required `new_records` (`bootstrap_only` | `query_allowed`)
- Baseball player bind: `player` + `debut_team` + `debut_year` (one row per `lahman.playerID`; no appearance-driven bind aliases)
- Partial `{player}` 0-hit on `bootstrap_only` → `not_found` (not `lookup_incomplete`)
- Legacy manifest keys fail fast (`grains`, `default_grain`, `identity_mode`, `seed_grain`)

## Changes

| Area | Change |
|------|--------|
| `src/network/mvr.py` | `RecordTypePolicy`, `infer_record_type_from_lookup`, `is_bootstrap_only_record_type` |
| `src/agents/*`, `delivery`, `paths`, bootstrap | `grain` → `record_type` throughout |
| `target_resolve.py` | Partial bootstrap-only 0-hit delegates to `_resolve_bootstrap_only_zero_hit` |
| `responses.py` / `dispatch.py` | Multi-record-type identity shaping on step-2 deliver |
| `lahman_common.py` | `distinct_player_debut_rows()` SQL |
| `lahman_seed.py` | One `ensure_entity_bind_fields` per playerID |
| Manifests | baseball, crm, empty-crm, crm-metering |
| Docs | `query-record-type-router.md` (renamed); seed-bootstrap, architecture, hand plan |
| Tests | `test_strict_record_type_routing.py`, `test_multi_record_type_entity_stores.py` |
| Smoke | `bin/smoke-baseball-e2e` debut bind; default example manifest for import |

## Routing contract (baseball)

| Lookup keys | Record type | Step-1 (typical) |
|-------------|-------------|------------------|
| `{player, debut_team, debut_year}` | player | `lookup_resolved` |
| `{player}` only | player | resolved / multi-match / `not_found` |
| `{team}` | team | `lookup_resolved` |
| `{player, team}` legacy | — | `not_found` |

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **506** smoke passed |
| `./bin/smoke-baseball-e2e` | **6/6** |
| `./bin/smoke-crm-e2e` | **7/7** |

## Paul post-slice (required)

**Re-bootstrap** baseball network root — old `player`+`team` entity stores are invalid.

```bash
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root "${ROOT:-/tmp/mycelium-baseball-benchmark}" --yes --no-default
```

Update live `~/mycelium-networks/*` manifests if graphs fail at import (legacy `mvr.grains` rejected).

Hand tests after re-bootstrap:

```bash
export MYCELIUM_NETWORK_ROOT="$ROOT"
./bin/baseball-query '{"lookup": {"player": "Hank Aaron"}}'
./bin/baseball-query '{"lookup": {"player": "Nobody Here"}}'  # → not_found
./bin/baseball-query '{"lookup": {"player": "Hank Aaron", "debut_team": "Milwaukee Braves", "debut_year": "1954"}}'
```

## For Grok + Paul

- **Breaking:** manifest vocabulary + baseball bind shape; CRM unchanged behavior with `new_records: query_allowed`.
- **Doc link:** `docs/query-grain-router.md` → `docs/query-record-type-router.md` (update HOLD.md / any external refs).
- **Hand test plan:** Q05 → `not_found`; full queries use `debut_team`/`debut_year` (many legacy `{player, team}` rows in plan still need Paul pass — header + matrix updated).
- **HOLD.md:** Mark 1800 done; note re-bootstrap gate.
- No commit (per workflow).

**Suggested commit message:**

```
feat(mvr): record_type + new_records; baseball player debut bind

Rename grain vocabulary to record_type/new_records; player bind uses
debut_team/debut_year; bootstrap_only partial 0-hit returns not_found.
```

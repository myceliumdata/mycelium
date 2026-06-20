# Lookup-key record-type routing

Multi-record-type networks route step-1 lookups by **lookup key shape** — not fan-out, not `EntityQuery.record_type`, not a disambiguation LLM. Each record type declares disjoint `bind_fields` in `network.json`; the client sends keys that match exactly one record type.

See also [architecture.md](architecture.md) § Target protocol and [seed-bootstrap.md](seed-bootstrap.md) § bind alias vs field alias.

## Baseball contract (locked)

| Lookup keys | Record type | Meaning |
|-------------|-------------|---------|
| `player` + `debut_team` + `debut_year` | `player` | Full MVR — one Lahman catalog row |
| `player` + `debut_team` | `player` | Partial (year missing) |
| `player` only | `player` (partial) | Field index; unique → `lookup_resolved`; homonyms → multi-match; 0-hit → fuzzy → LLM alias → `lookup_suggested` / `lookup_resolved` / `not_found` |
| `team` only | `team` | Fan-facing franchise label |
| `{player, team}` (legacy) | — | `not_found` (`team` is not a player bind field) |
| Other / unknown keys | — | `not_found` |

Manifest (`examples/networks/baseball/network.json`):

- `player` record type: `bind_fields: ["player", "debut_team", "debut_year"]`, `new_records: "bootstrap_only"`
- `team` record type: `bind_fields: ["team"]`, `new_records: "bootstrap_only"`

## Framework behavior

`infer_record_type_from_lookup()` in `network/mvr.py`:

1. Normalize lookup keys via `normalized_lookup_values`.
2. Find record types whose `bind_fields` set **equals** the lookup key set exactly.
3. **One match** → `_resolve_single_record_type_step1` on that record type.
4. **Zero matches** → `lookup_incomplete` when keys are a strict subset of one record type's bind fields (then multi-record-type step-1 **delegates** to `_resolve_single_record_type_step1` — field index, fuzzy, then incomplete or `not_found` for `bootstrap_only`); else `not_found`. Single-record-type networks call `_resolve_single_record_type_step1` directly.
5. **Two+ matches** → should not occur with disjoint field names.

`id`-only step 1 still uses `resolve_id_all_record_types` (search all stores; no LLM).

## `new_records` policy

| Value | Partial 0-hit | Full MVR 0-hit |
|-------|---------------|----------------|
| `query_allowed` (CRM) | fuzzy → `lookup_suggested`, else `lookup_incomplete` + `required_fields` | fuzzy → `lookup_suggested`, else `create_pending` |
| `bootstrap_only` (baseball) | fuzzy → `lookup_suggested`, else LLM alias → `lookup_resolved` / `not_found` | same; never `create_pending` |

## Delivery scope

`DeliveryScope.record_type` is set at issue time from the inferred record type. Step 2 loads the matching registry via `scope.record_type`.

## Query scope (M9)

Step 1 may include optional **`scope`** on `EntityQuery` (top-level sibling of `lookup`, not nested under bind keys):

```json
{
  "lookup": {"team": "Brooklyn Dodgers"},
  "scope": {"yearID": "1957"},
  "requested_attributes": ["season_wins"]
}
```

- Bound on `DeliveryScope.query_scope` at issue time; step 2 replays via internal graph state (`delivery_scope_query_scope`).
- **`team_season`**: `team_latest_column` aliases use scoped `yearID` when present; omit scope for latest year per `teamID` (M6 default).
- **`career_sum` / `career_era_weighted`**: ignore `yearID` (career totals).
- Future **`season_column`** aliases require `yearID` (season-scoped pull).
- Provenance `parameters.yearID` is set when scope was applied.

## Removed (slice 1100)

- Multi-grain fan-out (`query_grain_router.py`)
- Grain-disambiguation LLM (`grain_disambiguation.py`)
- `EntityQuery.grain` step-1 override

## Bind-index fallback (slice 1000)

Full MVR lookup on a record type consults `bind_index` when field-index AND misses. Baseball player bootstrap uses one primary bind per `playerID` (no appearance-driven alias explosion).

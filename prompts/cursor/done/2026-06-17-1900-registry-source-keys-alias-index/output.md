# Output — registry source_keys and field alias index

## Summary

Extended the entity registry with persisted `source_keys`, `field_aliases`, and `source_key_index`. Lahman bootstrap dedups players via `lookup_by_source_key("lahman.playerID", …)` instead of an in-memory map; teams get `lahman.teamID` / `lahman.franchID`. Field aliases index shared nicknames without touching `bind_index`. `./bin/ci-local` green at **480** smoke tests.

## Files changed (high level)

| Area | Change |
|------|--------|
| `entity_registry.py` | `RegistryEntity.source_keys`, `field_aliases`; `EntitiesDocument.source_key_index`; `lookup_by_source_key`, `set_source_keys`, `add_field_alias`; rebuild index on load/save (including deferred bootstrap) |
| `field_index.py` | `build_field_indexes` merges `field_aliases` |
| `lahman_common.py` | `distinct_team_label_rows()` with representative `teamID` / `franchID` |
| `lahman_seed.py` | Dropped `player_ids` dict; source key lookup + `set_source_keys` on create |
| Tests | `test_lookup_by_source_key_round_trip`, `test_add_field_alias_allows_multi_entity_lookup`; Lahman asserts `source_keys` |
| Docs | `seed-bootstrap.md`, baseball README, `baseball-example-program.md` identity table |

## Disk shape

Per-grain entity document (`entities/<grain>.json` or minisql payload):

```json
{
  "entities": {
    "<uuid>": {
      "id": "...",
      "bind_values": { "name": "Brooklyn Dodgers" },
      "source_keys": { "lahman.teamID": "BRO", "lahman.franchID": "LAD" },
      "field_aliases": { "name": ["Dodgers"] }
    }
  },
  "bind_index": { "brooklyn dodgers": "<uuid>" },
  "source_key_index": { "lahman.teamID|BRO": "<uuid>" }
}
```

- **`source_key_index`** is **rebuilt from `entities[].source_keys` on load and before save** (persisted for inspection; authoritative data lives on entity rows).
- **`field_aliases`** are **not** in `bind_index`; they feed in-memory field indexes only (rebuilt on load/save).
- **`add_bind_alias`** unchanged: `bind_index` only, skips field-index rebuild.

## Exit criteria

| # | Status |
|---|--------|
| E1 | No `player_ids` in `lahman_seed.py` |
| E2 | `lookup_by_source_key("lahman.playerID", …)` works after bootstrap |
| E3 | `add_field_alias` — two teams + `"Dodgers"` → `lookup_by_target_lookup` returns 2 ids |
| E4 | Multi-team same `playerID` test passes |
| E5 | `./bin/ci-local` green — **480** smoke tests |
| E6 | Disk shape documented above |

## For Grok + Paul

- **EntityStore / minisql migration:** new fields use Pydantic defaults; existing JSON loads without migration. `source_key_index` backfills on first load/save after upgrade.
- **Slice 2** (`2026-06-17-2000-baseball-closed-identity-lazy-aliases`) can build on `add_field_alias` for lazy LLM nicknames.
- **Collision policy:** if two entities share the same namespaced source key value, rebuild keeps the last entity id in iteration order (should not occur for Lahman `playerID`).

**Suggested commit message:**

```
feat(registry): source_keys and field alias index

Persist Lahman source IDs on RegistryEntity; field aliases for
multi-entity nickname lookup; Lahman handler drops in-memory playerID map.
```

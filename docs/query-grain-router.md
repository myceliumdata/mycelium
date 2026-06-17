# Lookup-key grain routing

Multi-grain networks route step-1 lookups by **lookup key shape** — not fan-out, not `EntityQuery.grain`, not a disambiguation LLM. Each grain declares disjoint `bind_fields` in `network.json`; the client sends keys that match exactly one grain.

See also [architecture.md](architecture.md) § Target protocol and [seed-bootstrap.md](seed-bootstrap.md) § bind alias vs field alias.

## Baseball contract (locked)

| Lookup keys | Grain | Meaning |
|-------------|-------|---------|
| `player` + `team` | `player` | Person on a roster |
| `team` only | `team` | Fan-facing franchise label |
| `player` only | `player` (partial) | Try field index on player grain (CRM parity); unique hit → `lookup_resolved`; homonyms → multi-match; 0-hit → `lookup_incomplete` (`required_fields: ["team"]`) |
| Other / unknown keys | — | `not_found` or `lookup_incomplete` |

Manifest (`examples/networks/baseball/network.json`):

- `player` grain: `bind_fields: ["player", "team"]`
- `team` grain: `bind_fields: ["team"]`

## Framework behavior

`infer_grain_from_lookup()` in `network/mvr.py`:

1. Normalize lookup keys via `normalized_lookup_values`.
2. Find grains whose `bind_fields` set **equals** the lookup key set exactly.
3. **One match** → `_resolve_single_grain_step1` on that grain.
4. **Zero matches** → `lookup_incomplete` when keys are a strict subset of one grain's bind fields (then multi-grain step-1 **delegates** to `_resolve_single_grain_step1` on that grain — field index, fuzzy, then incomplete); else `not_found`. Single-grain networks already call `_resolve_single_grain_step1` directly.
5. **Two+ matches** → should not occur with disjoint field names.

`id`-only step 1 still uses `resolve_id_all_grains` (search all stores; no LLM).

## Delivery scope

`DeliveryScope.grain` is set at issue time from the inferred grain. Step 2 loads the matching registry via `scope.grain`.

## Removed (slice 1100)

- Multi-grain fan-out (`query_grain_router.py`)
- Grain-disambiguation LLM (`grain_disambiguation.py`)
- `EntityQuery.grain` step-1 override

## Bind-index fallback (slice 1000)

Full MVR lookup on a grain consults `bind_index` when field-index AND misses (multi-team player aliases). See [seed-bootstrap.md](seed-bootstrap.md).

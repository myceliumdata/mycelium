# Record-type routing (player vs team)

## What this demonstrates

**Lookup key set infers record type** — no fan-out. `{player: …}` routes to the player registry; `{team: …}` routes to the team registry.

## Prerequisites

Bootstrapped baseball root.

## How to test — CLI

```bash
# Player
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}'

# Team (fan-facing city+name label)
uv run mycelium query --network baseball \
  --lookup-json '{"team":"Boston Red Sox"}'
```

Deliver each with step 2 `--delivery-id` as usual.

## How to test — MCP

```json
{ "lookup": { "team": "Boston Red Sox" } }
```

Then step 2 with `delivery_id`.

## Expected output

| Lookup | Record type | Step 1 |
|--------|-------------|--------|
| `player: Hank Aaron` | `player` | `lookup_resolved` |
| `team: Boston Red Sox` | `team` | `lookup_resolved` |

Step 2 identity rows reflect the active MVR bind fields for that record type.

## Learn more

- [query-record-type-router.md](../../../plans/query-record-type-router.md)
- Live gate: `bb-multi-01` (player + team in one session)
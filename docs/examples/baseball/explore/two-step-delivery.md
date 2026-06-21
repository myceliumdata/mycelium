# Two-step delivery (baseball)

## What this demonstrates

The **target query protocol**: step 1 resolves a lookup and returns `delivery.delivery_id`; step 2 delivers identity or requested attributes. Core to all Mycelium networks.

## Prerequisites

`./bin/refresh-example-network baseball --yes` (or live root already bootstrapped).

## How to test — CLI

```bash
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}'
# Copy delivery_id from JSON

uv run mycelium query --network baseball --delivery-id d_PASTE_HERE
```

## How to test — MCP

**Step 1** — `query_entity`:

```json
{
  "lookup": { "player": "Hank Aaron" }
}
```

**Step 2** — `query_entity`:

```json
{
  "delivery_id": "d_…"
}
```

Use the same MCP server bound to `MYCELIUM_NETWORK=baseball`.

## Expected output

| Step | `outcome` | Notable fields |
|------|-----------|----------------|
| 1 | `lookup_resolved` | `delivery.delivery_id`, `total_matches: 1`, empty or partial `results[]` |
| 2 | `assembled` | `results[0]` with player bind fields (`player`, `debut_team`, `debut_year`) |

## Learn more

- [MVR redesign examples](../../../plans/mvr-redesign-entity-query-examples.md)
- Live gate: `bb-identity-01` in [`tests/live/catalogs/baseball.yaml`](../../../../tests/live/catalogs/baseball.yaml)
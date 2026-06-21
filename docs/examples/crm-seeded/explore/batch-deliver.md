# Batch deliver (multi-match)

## What this demonstrates

One lookup matching **multiple registry rows** — step 2 delivers all matches in `results[]`.

## Prerequisites

CRM refreshed.

## How to test — CLI

```bash
uv run mycelium query --network crm-seeded \
  --lookup-json '{"employer":"645 Ventures"}'
uv run mycelium query --network crm-seeded --delivery-id d_…
```

## How to test — MCP

Use fixtures in [`examples/networks/crm-seeded/queries/`](../../../../examples/networks/crm-seeded/queries/):

1. `01-resolve-batch.json` → copy `delivery_id`
2. `02-deliver-batch.json` with that id

## Expected output

| Step | `outcome` | Notable |
|------|-----------|---------|
| 1 | `lookup_resolved` | `total_matches: 3` |
| 2 | `assembled` | `results.length === 3` |

## Learn more

- [entity-protocol examples](../../../plans/mvr-redesign-entity-query-examples.md)
- Live gate: `crm-protocol-02`
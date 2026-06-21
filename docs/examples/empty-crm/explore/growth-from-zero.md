# Growth from zero

## What this demonstrates

**Cold-start network** — no bootstrap import; first registry row created on step 2 deliver with `create_on_deliver` from step 1.

## Prerequisites

`./bin/refresh-example-network empty-crm --yes`

Optional for email on step 1: `OPENAI_API_KEY` + search provider key.

## How to test — CLI

```bash
uv run mycelium network status --network empty-crm
# entity_count: 0

uv run mycelium query --network empty-crm \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'

uv run mycelium query --network empty-crm --delivery-id d_…
```

## How to test — MCP

```json
"env": { "MYCELIUM_NETWORK": "empty-crm" }
```

```json
{ "lookup": { "name": "Paul Murphy", "employer": "Acme Corp" } }
```

## Expected output

| Step | `outcome` | Notes |
|------|-----------|-------|
| 1 | `lookup_resolved` | `create_on_deliver: true` |
| 2 | `assembled` | First row in `entities/person.json` |

`network status` afterward: `entity_count: 1`.

## Learn more

- [`examples/networks/empty-crm/README.md`](../../../../examples/networks/empty-crm/README.md)
- Live gate: `empty-growth-01`
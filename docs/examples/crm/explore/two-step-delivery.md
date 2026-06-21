# Two-step delivery (CRM)

## What this demonstrates

Target protocol on the default **person** MVR (`name` + `employer`).

## Prerequisites

`./bin/refresh-example-network crm --yes`

## How to test — CLI

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name":"Nichanan Kesonpat","employer":"1k(x)"}'
uv run mycelium query --network crm --delivery-id d_…
```

## How to test — MCP

```json
{
  "lookup": { "name": "Nichanan Kesonpat", "employer": "1k(x)" }
}
```

## Expected output

| Step | `outcome` |
|------|-----------|
| 1 | `lookup_resolved` + `delivery.delivery_id` |
| 2 | `assembled` — `results[0].name`, `results[0].employer` |

## Learn more

- [mvr-redesign-entity-query-examples.md](../../../plans/mvr-redesign-entity-query-examples.md)
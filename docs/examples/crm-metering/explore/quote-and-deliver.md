# Quote and deliver (metering)

## What this demonstrates

**Entity metering** — requesting a researched attribute on step 1 can return `quote_required`; step 2 deliver includes `quote_id` from the quote response.

## Prerequisites

```bash
./bin/refresh-example-network crm-metering --yes
OPENAI_API_KEY=…
# + active SEARCH_PROVIDER key
```

Restart MCP with `MYCELIUM_NETWORK=crm-metering`.

## How to test — CLI

```bash
uv run mycelium query --network crm-metering \
  --lookup-json '{"name":"Paul Murphy","employer":"PRM"}' \
  --requested-attributes email
# outcome: quote_required — copy delivery_id and quote.quote_id

uv run mycelium query --network crm-metering \
  --delivery-id d_… --quote-id q_…
```

## How to test — MCP

Use [`examples/networks/crm-metering/queries/`](../../../../examples/networks/crm-metering/queries/) in order:

| Step | File | Expected |
|------|------|----------|
| 1 | `01-resolve-lookup.json` | `lookup_resolved` |
| 2 | `02-quote-email.json` | `quote_required` |
| 3 | `03-deliver-quote.json` | `assembled` (paste ids) |

## Expected output

| Step | `outcome` |
|------|-----------|
| Quote step | `quote_required` with `quote.quote_id` |
| Deliver | `assembled` with `email` researched |

## Learn more

- [architecture.md](../../../architecture.md) § Metering
- Live gate: `meter-01-quote`, `meter-02-deliver`
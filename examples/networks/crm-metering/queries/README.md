# MCP query fixtures — Paul Murphy metering arc (target protocol)

Use with an MCP server bound to **`crm-metering`** (`MYCELIUM_NETWORK=crm-metering` or `MYCELIUM_NETWORK_ROOT`). Restart MCP after `./bin/refresh-example-network crm-metering`.

Call **`describe_network`** first, then paste each JSON into **`query_entity`** in order.

| Step | File | Expected outcome |
|------|------|------------------|
| 1 | `01-resolve-lookup.json` | `lookup_resolved` — copy `delivery.delivery_id` |
| 2 | `02-quote-email.json` | `quote_required` — copy `delivery.delivery_id` and `quote.quote_id` |
| 3 | `03-deliver-quote.json` | Replace placeholders → `assembled` |

Step 3 replaces placeholders with `delivery_id` and `quote_id` from the step-2 `quote_required` response.

Step 3 needs API keys in `.env` for live email research on a cold network.

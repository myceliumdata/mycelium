# MCP query fixtures — Paul Murphy metering arc (target protocol)

Use with an MCP server bound to **`crm-metering`** (`MYCELIUM_NETWORK=crm-metering` or `MYCELIUM_NETWORK_ROOT`). Restart MCP after `./bin/refresh-example-network crm-metering`.

Call **`describe_network`** first, then paste each JSON into **`query_entity`** in order.

| Step | File | Expected outcome |
|------|------|------------------|
| 1 | `01-resolve-lookup.json` | `lookup_resolved` — copy `delivery.delivery_id` |
| 2 | `02-quote-email.json` | `quote_required` — copy `delivery.delivery_id` and `quote.quote_id` |
| 3 | `03-deliver-quote.json` | Replace placeholders → `assembled` |

Step 2 binds attrs into the delivery scope; step 3 delivers with `delivery_id` + `quote_id` only.

Step 3 needs API keys in `.env` for live email research on a cold network.

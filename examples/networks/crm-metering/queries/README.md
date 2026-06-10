# MCP query fixtures — Paul Murphy metering arc

Use with a MCP server bound to **`crm-metering`** (`MYCELIUM_NETWORK=crm-metering` or `MYCELIUM_NETWORK_ROOT`). Restart MCP after `./bin/refresh-example-network crm-metering`.

Call **`describe_network`** first, then paste each JSON into **`query_entity`** in order.

| Step | File | Expected outcome |
|------|------|------------------|
| 1 | `01-bind.json` | `entity_validated` |
| 2 | `02-quote-email.json` | `quote_required` — copy `quote.quote_id` |
| 3 | `03-accept-quote.json` | Replace `"<quote_id-from-step-2>"` with the id from step 2 → `assembled` |

Step 3 needs API keys in `.env` for live email research on a cold network.

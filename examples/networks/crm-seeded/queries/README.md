# MCP query fixtures — batch deliver (target protocol)

Use with **`crm-seeded`** network. Three matches for `employer: 645 Ventures`.

| Step | File | Expected outcome |
|------|------|------------------|
| 1 | `01-resolve-batch.json` | `lookup_resolved` with `total_matches: 3` |
| 2 | `02-deliver-batch.json` | `assembled` with 3 rows in `results[]` |

Paste JSON into **`query_entity`**; copy `delivery.delivery_id` from step 1 into step 2.

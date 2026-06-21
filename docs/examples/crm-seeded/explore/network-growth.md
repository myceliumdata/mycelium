# Network growth (new person)

## What this demonstrates

**Query-time registry growth** on `query_allowed` CRM — step 1 with unknown MVR returns `create_on_deliver`; step 2 creates the row and runs specialists.

## Prerequisites

CRM refreshed (or use [`crm-empty`](../crm-empty/getting-started.md) for zero seed).

## How to test — CLI

```bash
uv run mycelium query --network crm-seeded \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'
# If lookup_suggested for collision, follow suggestion or pass confirm_new_entity

uv run mycelium query --network crm-seeded --delivery-id d_… \
  --requested-attributes email
```

Requires research keys if requesting `email`.

## How to test — MCP

```json
{
  "lookup": { "name": "Paul Murphy", "employer": "Acme Corp" },
  "requested_attributes": ["email"]
}
```

## Expected output

Step 1: `lookup_resolved` with `delivery.create_on_deliver: true` when no match.

Step 2: new `entity_id` in registry; specialist storage written.

## Learn more

- [examples/networks/crm-seeded/README.md](../../../../examples/networks/crm-seeded/README.md) § Network growth
- Contrast: [crm-empty growth walkthrough](../crm-empty/explore/growth-from-zero.md)
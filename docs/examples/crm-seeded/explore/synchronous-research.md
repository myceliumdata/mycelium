# Synchronous research (email)

## What this demonstrates

**Specialist research Phase 1** — cache miss on `email` runs inline LLM + `web_search`; result persisted under `agents/<category>/storage.json`.

## Prerequisites

```bash
OPENAI_API_KEY=…
SEARCH_PROVIDER=tavily   # or exa / brave + matching key
```

`./bin/refresh-example-network crm-seeded --yes` for cold cache. First hit: **tens of seconds**.

## How to test — CLI

```bash
uv run mycelium query --network crm-seeded \
  --lookup-json '{"name":"Andrea Kalmans","employer":"Lontra Ventures"}' \
  --requested-attributes email
uv run mycelium query --network crm-seeded --delivery-id d_…
```

## How to test — MCP

```json
{
  "lookup": { "name": "Andrea Kalmans", "employer": "Lontra Ventures" },
  "requested_attributes": ["email"],
  "thread_id": "crm-email-demo"
}
```

## Expected output

Step 2 `assembled` with `results[0].email` populated (research-derived). Repeat query: fast cache hit.

## Learn more

- [specialist-research-phase1.md](../../../plans/specialist-research-phase1.md)
- Live gate: `crm-research-01`
# Provenance envelope

## What this demonstrates

**Computation-centric provenance** — step 1 with `--provenance` (or MCP `provenance: true`) causes step 2 to attach `provenance` on each result: `sources[]`, `computation`, `parameters`.

## Prerequisites

Bootstrapped baseball root. Derive attrs need derive keys; manifest attrs work without.

## How to test — CLI

```bash
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes career_hr \
  --provenance
# step 2 with delivery_id
```

## How to test — MCP

```json
{
  "lookup": { "player": "Hank Aaron" },
  "requested_attributes": ["career_hr"],
  "provenance": true
}
```

## Expected output

Step 2 `results[0].provenance` includes:

- `sources` — Lahman dataset pin / warehouse path
- `computation` — resolver or inline derive code
- `parameters` — requested attribute, entity keys, scope

Derived stats show `computation.inline` with sandbox codegen on first miss.

## Learn more

- [computation-centric-provenance.md](../../../plans/conversations/2026-06-18-computation-centric-provenance.md)
- [architecture.md](../../../architecture.md) § Provenance
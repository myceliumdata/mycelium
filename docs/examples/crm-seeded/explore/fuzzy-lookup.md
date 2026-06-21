# Fuzzy lookup suggestions

## What this demonstrates

On 0 exact bind-index hits, the framework suggests **corrected lookups** (typos, first-token prefix) via `lookup_suggested` + `suggestions[].suggested_lookup`.

## Prerequisites

CRM refreshed.

## How to test — CLI

```bash
uv run mycelium query --network crm-seeded \
  --lookup-json '{"name":"Andrea Kalman"}'
```

Retry step 1 with suggested lookup:

```bash
uv run mycelium query --network crm-seeded \
  --lookup-json '{"name":"Andrea Kalmans"}'
```

## How to test — MCP

```json
{ "lookup": { "name": "Andrea Kalman" } }
```

## Expected output

| Input | `outcome` | Retry |
|-------|-----------|-------|
| `Andrea Kalman` | `lookup_suggested` | `{"name":"Andrea Kalmans"}` |
| `Andrea Kalmans` | `lookup_resolved` | — |

`reason`: `fuzzy_bind_field_match` on suggestions.

## Learn more

- [fuzzy-lookup-policy.md](../../../plans/fuzzy-lookup-policy.md)
- Live gate: `crm-negative-01`
# Warehouse manifest stats

## What this demonstrates

**Manifest-driven warehouse pulls** — attributes aliased in `warehouse_domains.json` resolve via SQL against `lahman.sqlite` without LLM derive.

## Prerequisites

Bootstrapped baseball root. No derive keys required for manifest-only stats.

## How to test — CLI

```bash
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes career_hr
# step 2 with delivery_id
```

## How to test — MCP

```json
{
  "lookup": { "player": "Hank Aaron" },
  "requested_attributes": ["career_hr"]
}
```

Then step 2 with `delivery_id`.

## Expected output

| Field | Approximate value (Lahman v2025 root) |
|-------|----------------------------------------|
| `outcome` (step 2) | `assembled` |
| `results[0].career_hr` | **755** |

Provenance (optional): add `--provenance` on step 1; step 2 includes `provenance` with warehouse computation metadata.

## Learn more

- [baseball-example-program.md](../../../plans/baseball-example-program.md) § Warehouse factory
- [specialist-class-hierarchy.md](../../../architecture/whys/specialist-class-hierarchy.md)
- Live gate: `bb-m2-01`, `bb-pitch-01`
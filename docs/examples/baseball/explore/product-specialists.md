# Product specialists (roster, franchise)

## What this demonstrates

**Product-tier specialists** — coherent multi-row artifacts (roster list, franchise team labels) from warehouse joins, distinct from single-stat warehouse domains.

## Prerequisites

Bootstrapped baseball root.

## How to test — CLI

```bash
# Scoped roster — 1957 Boston Red Sox
uv run mycelium query --network baseball \
  --lookup-json '{"team":"Boston Red Sox"}' \
  --scope-json '{"yearID":"1957"}' \
  --requested-attributes roster

# Franchise team labels (fan team → related labels)
uv run mycelium query --network baseball \
  --lookup-json '{"team":"Boston Red Sox"}' \
  --requested-attributes franchise_teams
```

Step 2 after each step 1.

## How to test — MCP

```json
{
  "lookup": { "team": "Boston Red Sox" },
  "scope": { "yearID": "1957" },
  "requested_attributes": ["roster"]
}
```

## Expected output

| Attribute | Shape |
|-----------|--------|
| `roster` | String or list containing **Hank Aaron** for 1957 BRO membership in gate anchors |
| `franchise_teams` | JSON list of related team labels (e.g. Brooklyn/LA Dodgers lineage for other franchises) |

`outcome`: `assembled`.

## Learn more

- [specialist-class-hierarchy.md](../../../architecture/whys/specialist-class-hierarchy.md) — product tier
- Live gate: `bb-roster-01`, `bb-franchise-01`
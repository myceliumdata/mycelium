# Query scope (`yearID`)

## What this demonstrates

**Scoped warehouse queries** — `scope.yearID` on step 1 limits team-season facts to one season (e.g. 1957 roster, season W/L).

## Prerequisites

Bootstrapped baseball root.

## How to test — CLI

```bash
uv run mycelium query --network baseball \
  --lookup-json '{"team":"Boston Red Sox"}' \
  --scope-json '{"yearID":"1957"}' \
  --requested-attributes season_wins,season_losses
```

Step 2 with `delivery_id`.

## How to test — MCP

```json
{
  "lookup": { "team": "Boston Red Sox" },
  "scope": { "yearID": "1957" },
  "requested_attributes": ["season_wins", "season_losses"]
}
```

## Expected output

Step 2 `assembled` with `season_wins` / `season_losses` for **1957** only (not career aggregates).

Roster with scope: `requested_attributes: ["roster"]` + same `yearID` returns member names for that season.

## Learn more

- Live gate: `bb-team-01`, `bb-roster-01`
- Slice `2026-06-20-2220-baseball-query-scope-yearid-m9`
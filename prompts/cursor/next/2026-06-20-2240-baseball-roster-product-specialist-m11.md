# Baseball roster product specialist (M11)

> **READY** — Cross-record-type **product** specialist (not supervisor fan-out). **Do not edit `TODO.md`.**

## Objective

**`roster_specialist`** (or `team_roster_specialist`): given **team** entity + optional `yearID` scope, return roster artifact — list of player display names / ids from `Appearances` ⋈ `People`.

## Design locks (from program doc)

- Single coherent computation + unified cache key (`teamID` + `yearID`).
- Provenance: `parameters.lahman.teamID`, `parameters.yearID`, `warehouse`, `computation.inline`.
- New category in `categories.json` e.g. `team_roster` with attr `roster` or `roster_players` (string JSON array — shape TBD in output.md).

## Query contract

- Step 1: `{team: "Brooklyn Dodgers"}` + `requested_attributes: ["roster"]` (+ scope when M9 ships).
- Step 2: deliver merged result from one specialist (not batting+bio fan-out).

## Tests

- Minimal fixture: 1957 BRO roster includes Hank Aaron.
- Smoke + optional live-gate scenario after Paul reloads Lahman.
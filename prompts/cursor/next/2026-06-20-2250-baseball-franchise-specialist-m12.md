# Baseball franchise product specialist (M12)

> **READY** — Emergent cross-team aggregation. **Do not edit `TODO.md`.**

## Objective

**`franchise_specialist`**: on request (e.g. `franchise_teams` or client pushback attr), aggregate fan-facing team identities sharing `lahman.franchID` (Brooklyn + LA Dodgers).

## v1 scope

- Read `TeamsFranchises` + `Teams` warehouse tables.
- Return canonical list of team labels or franchise metadata — not default record type; opt-in attribute.
- Registry `team` entities unchanged.

## Tests

- Fixture with BRO + LAN sharing `franchID=LAD`.
- Smoke deliver on franchise attr; provenance cites warehouse + `franchID` parameter.

## Non-goals

- Auto-merge team registry rows.
- Web research.
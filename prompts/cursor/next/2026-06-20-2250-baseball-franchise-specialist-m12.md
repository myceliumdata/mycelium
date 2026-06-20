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

## Live gate (required)

Add **`bb-franchise-01`** to `tests/live/catalogs/baseball.yaml` (new phase `franchise` in `networks.yaml`):

- Dodgers franchise query — deliver includes both Brooklyn and Los Angeles team labels (or canonical franchise metadata per v1 shape).
- Anchor `franchise_team_labels` (sorted list or count) from live Lahman root.
- Drift check in `gate_runner.py`.

`@pytest.mark.live_gate` only — never default CI.

## Non-goals

- Auto-merge team registry rows.
- Web research.
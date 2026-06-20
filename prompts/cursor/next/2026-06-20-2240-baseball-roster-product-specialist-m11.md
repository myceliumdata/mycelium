# Baseball roster product specialist (M11)

> **READY** — Cross-record-type **product** specialist (not supervisor fan-out). **Do not edit `TODO.md`.**

## Objective

**`roster_specialist`** (or `team_roster_specialist`): given **team** entity + optional `yearID` scope, return roster artifact — list of player display names / ids from `Appearances` ⋈ `People`.

## Pack pattern (mandatory)

This is a **product specialist** (cross-table join), not a manifest `career_sum` read. **Do not** wire it through `run_warehouse_player_graph` / `run_warehouse_team_graph` unless you add a deliberate new helper in `pack_common.py` (e.g. `run_product_team_graph`) that fits the pattern.

- New `roster_specialist.py` still needs the **`pack_bootstrap` block** (copy from `pitching_specialist.py`) if it imports sibling pack modules.
- Prefer one cohesive graph function in the specialist file or a focused `roster_common.py` sibling — not a copy of the old 200-line warehouse loop.

## Design locks (from program doc)

- Single coherent computation + unified cache key (`teamID` + `yearID`).
- Provenance: `parameters.lahman.teamID`, `parameters.yearID`, `warehouse`, `computation.inline`.
- New category in `categories.json` e.g. `team_roster` with attr `roster` or `roster_players` (string JSON array — shape TBD in output.md).

## Query contract

- Step 1: `{team: "Brooklyn Dodgers"}` + `requested_attributes: ["roster"]` (+ scope when M9 ships).
- Step 2: deliver merged result from one specialist (not batting+bio fan-out).

## Tests

- Minimal fixture: 1957 BRO roster includes Hank Aaron.
- Smoke deliver + provenance on roster attr.

## Live gate (required)

Add **`bb-roster-01`** to `tests/live/catalogs/baseball.yaml` (new phase `roster` in `networks.yaml`):

- `{team: "{{ anchors.team_label }}"}` + `scope: {yearID: "1957"}` + `requested_attributes: [roster]` (attr name per your design lock).
- Anchor `roster_count_1957_bro` or similar stable assertion (e.g. minimum player count, or includes `"Hank Aaron"` substring in delivered roster) — discover from live root.
- Drift check in `gate_runner.py` if numeric anchor used.

`@pytest.mark.live_gate` only — never default CI.
# Baseball query scope — yearID / teamID (M9)

> **READY** — Framework + pack. **Do not edit `TODO.md`.**

## Objective

Allow season-scoped warehouse reads: client sends scope on step 1 (design lock with Paul/Grok in `output.md` if shape differs).

**Proposed v1:** optional `scope: {"yearID": "1957"}` on `EntityQuery` (or nested under `lookup` — pick one, document in `docs/query-record-type-router.md`).

## Behavior

- `team_season_specialist`: `season_wins` uses scoped year when present, else latest year (current M6 default).
- `batting_specialist` / `pitching_specialist`: season attrs (`wins`, `era`, …) filter warehouse by `yearID` when scoped.
- Provenance `parameters` includes `yearID` when used.

## Tests

- Smoke: Brooklyn Dodgers `season_wins` with `scope.yearID=1957` vs without (latest).
- Regression: existing career_sum attrs ignore scope (career totals).

## Live gate (required)

Add **`bb-team-02`** to `tests/live/catalogs/baseball.yaml` (phase `team_season`):

- Brooklyn Dodgers with explicit `scope: {yearID: "1957"}` + `season_wins` / `season_losses` — must match existing anchors (`season_wins: 84`, `season_losses: 70`).
- Keep **`bb-team-01`** (no scope, latest year) passing unchanged.

Optional: **`bb-scope-01`** — Aaron `career_hr` with a bogus `yearID` scope still returns career total (proves career_sum ignores scope).

Extend drift checks if new anchor keys are introduced.

`@pytest.mark.live_gate` only — never default CI.

## Constraints

- Backward compatible — omitting scope keeps current behavior.
- No CRM breakage.
# Baseball live gate — domain parity scenarios

> **READY** — After M5–M8 on Paul's machine (`--sync-only`). **Do not edit `TODO.md`.**

## Objective

Extend `tests/live/catalogs/baseball.yaml` with scenarios:

1. **bb-pitch-01** — Aaron `career_wins` anchor (warehouse sum).
2. **bb-team-01** — `{team: "…"}` + `season_wins` (scoped or latest per M9).
3. **bb-multi-01** — `career_hr` + `career_wins` same deliver.
4. **bb-pitch-02** — `career_era` approx anchor (after M8).

Update `tests/live/anchors/baseball_aaron_lahman_v2025.json` with pitching anchors from live root discovery.

## Docs

- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — move pitching/team_season from ❌ to ✅ where gated.

## Constraints

- `@pytest.mark.live_gate` only — never default CI.
- Use template anchors `{{ anchors.career_wins }}` pattern.
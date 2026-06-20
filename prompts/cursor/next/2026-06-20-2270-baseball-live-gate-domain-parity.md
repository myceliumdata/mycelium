# Baseball live gate — manual doc sync (M5–M6 complete)

> **READY** — Gate scenarios for M5–M6 **already landed** (Grok, 2026-06-20). Remaining `career_era` gate is in **M8** prompt. **Do not edit `TODO.md`.**

## Already shipped (do not redo)

| Scenario | Phase | Coverage |
|----------|-------|----------|
| `bb-pitch-01` | pitching | Aaron `career_wins` / `career_strikeouts` (zeros — path validation) |
| `bb-pitch-02` | pitching | Nolan Ryan wins + strikeouts |
| `bb-multi-01` | pitching | Aaron `career_hr` + `career_wins` |
| `bb-team-01` | team_season | Brooklyn Dodgers `season_wins` / `season_losses` |

Also shipped: anchors in `baseball_aaron_lahman_v2025.json`, `networks.yaml` phases (`pitching`, `team_season`), `gate_runner.py` drift for pitching + team season.

## Objective (this slice)

Update manual gate documentation only:

- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — move pitching / team_season rows from ❌ to ✅ where covered by live gate above.
- `docs/manual-checks/2026-06-20-live-gate-program.md` — note baseball catalog is **19 scenarios** and list new phase labels.

## Live gate (this slice)

**N/A** — no new catalog scenarios. If you discover doc/catalog drift while editing, fix docs only; file a remedial note in `output.md`.

## Constraints

- `@pytest.mark.live_gate` only — never default CI.
- `./bin/ci-local` must pass (smoke includes `test_load_catalog_baseball_has_minimum_scenarios`).
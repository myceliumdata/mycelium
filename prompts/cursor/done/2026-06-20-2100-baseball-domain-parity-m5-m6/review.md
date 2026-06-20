# Review — baseball domain parity M5–M6 (ad-hoc Grok)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-20  
**Commit:** `b6db456` (local; Paul pushes when ready)

## Context

Paul chose **option 2**: keep Grok’s implementation, formal review here, Cursor drains M7+ from `prompts/cursor/next/`. This was not a claimed Cursor slice; workflow retrofitted via this `done/` folder.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **621** smoke passed, ruff clean, admin-ui build ok |
| New tests | pitching (2), team_season (2), multi_domain (1) — all pass |

## Delivery

| Criterion | Result |
|-----------|--------|
| `pitching_specialist` pack module | Pass — `career_wins` = 5 on fixture |
| `team_identity_specialist` | Pass — clone of player_identity for `record_type=team` |
| `team_season_specialist` | Pass — `season_wins` = 84 (1957 BRO latest) |
| Table-aware `career_sum` (Pitching not Batting) | Pass |
| Multi-specialist `career_hr` + `career_wins` | Pass — both specialists in debug |
| Manifest aliases | Pass |
| M7–M13 Cursor queue | Pass — 8 prompts in `next/` |
| Program doc + TODO slice map | Pass |
| `TODO.md` by Grok (authorized) | Pass |
| CRM / framework regression | Pass (smoke) |

## Design critique

**Strong:** Correct pattern clone — pack specialists copied on `--sync-only`, manifest-driven resolve, provenance envelope matches M2b. `_domain_table` fixes latent bug where pitching `career_sum` would have hit Batting. Team season v1 (“latest year”) is documented and matches hand-test until M9 scope.

**Refactor (2026-06-20 follow-up):** `pack_common.py` + `registry_identity_common.py` deduplicate warehouse and identity graph paths; `bio_specialist`, `batting_specialist`, `pitching_specialist`, `team_season_specialist`, and identity specialists are thin wrappers. OSS-quality clarity — not deferred polish.

**Live gate (2026-06-20 follow-up):** Four new scenarios (`bb-pitch-01/02`, `bb-multi-01`, `bb-team-01`), anchors, `networks.yaml` phases, `gate_runner.py` drift checks. Baseball catalog **19 scenarios**.

## Polish nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| P1 | `bin/smoke-baseball-e2e` inline scenarios omit pitching/team_season (pytest only) | Optional inline rows or `--with-pytest` default note in README |
| P2 | `attendance` in ontology but no manifest alias | M6b or M9 |
| P3 | Manual gate hand-test doc not yet synced | M8 prompt (manual gate docs section) |
| P4 | `career_era` live gate | M8 `bb-pitch-03` |

## Next

Cursor: **work on the next task** → `2026-06-20-2200-baseball-bio-manifest-aliases-m7.md`.

Paul: push `b6db456` when ready; run `--sync-only` on live baseball root before hand-testing pitching/team season.
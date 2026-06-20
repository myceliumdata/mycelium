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

**Acceptable debt:** Near-duplicate specialist files (batting/pitching/team_season share ~200 lines). Acceptable for v1; a shared pack base module is a future polish slice, not blocking.

## Polish nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| P1 | `bin/smoke-baseball-e2e` inline scenarios omit pitching/team_season (pytest only) | Optional inline rows or `--with-pytest` default note in README |
| P2 | `attendance` in ontology but no manifest alias | M6b or M9 |
| P3 | Live gate unchanged — no Aaron `career_wins` anchor yet | `2270-live-gate-domain-parity` |
| P4 | Duplicated `_load_specialist_loader` in four pack modules | Shared helper in `specialist_loader.py` later |

## Next

Cursor: **work on the next task** → `2026-06-20-2200-baseball-bio-manifest-aliases-m7.md`.

Paul: push `b6db456` when ready; run `--sync-only` on live baseball root before hand-testing pitching/team season.
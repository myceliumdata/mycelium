# Review — baseball pitching career_era (M8)

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-20

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **628** smoke passed, ruff clean, admin-ui build ok |

## Delivery

| Criterion | Result |
|-----------|--------|
| `career_era_weighted` convention + resolver | Pass — pool `SUM(ER)` / `SUM(IPouts)` then `9*ER/IP` |
| Manifest alias `career_era` | Pass |
| `pitching_specialist` unchanged (thin wrapper) | Pass |
| Fixture ERA **3.000** (Aaron 9 ER / 81 outs) | Pass |
| Smoke + provenance tests | Pass |
| Live gate `bb-pitch-03` with float tolerance | Pass |
| Drift check `pitcher_career_era` ≈ 3.194 | Pass |
| Manual gate docs synced (hand-test + live-gate-program **21** scenarios) | Pass |
| `derive_on_miss` / season `era` deferred | Pass per prompt |
| `TODO.md` untouched | Pass |

## Design critique

**Strong:** Correct innings-weighted career formula documented in manifest conventions. Provenance uses `career_era_weighted` inline source. Gate `approx` + tolerance is appropriate for rate stats. Doc sync closes the M5–M6 manual gate gap.

**No blocking issues.**

## For Paul

- Live gate catalog **21** scenarios; phases include `pitching`, `team_season`.
- Commit bundled with M7.
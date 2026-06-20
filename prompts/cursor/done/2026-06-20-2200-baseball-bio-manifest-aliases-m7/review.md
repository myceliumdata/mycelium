# Review — baseball bio manifest aliases (M7)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-20

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **628** smoke passed, ruff clean, admin-ui build ok |

## Delivery

| Criterion | Result |
|-----------|--------|
| Five bio aliases in `warehouse_domains.json` | Pass |
| `people_compose_iso_date` + `death_date` compose | Pass |
| `people_birth_date` delegates to shared helper | Pass — no regression on birth_date path |
| Minimal fixture People.csv extended | Pass |
| Five new smoke tests (one per alias) | Pass |
| Live gate `bb-bio-01` + anchors + drift | Pass |
| Pack-only changes | Pass |
| `TODO.md` untouched | Pass |

## Design critique

**Strong:** `people_compose_iso_date` is the right generalization — `death_date` reuses the same convention machinery without duplicating SQL. Manifest entries are clear. Tests reuse `refresh_shared_fixture` consistently. Live gate drift extended for Aaron bio attrs.

**Acceptable:** `birth_date` manifest entry now lists explicit `columns` (was implicit via hardcoded helper). Improves symmetry with `death_date`; smoke suite confirms no regression.

## Polish nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | `bb-bio-01` gates height/weight/birth_country only; `final_game` / `death_date` are smoke-only | Optional `bb-bio-02` or extend `bb-bio-01` if Paul wants live gate on compose attrs |

## For Paul

- `./bin/refresh-example-network baseball --sync-only` then `./bin/gate-live baseball` on live root.
- Commit bundled with M8 (same working tree).
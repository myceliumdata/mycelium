# Review — baseball franchise product specialist (M12)

**Verdict:** **Approved + polish nits** (batch M10–M12)  
**Reviewer:** Grok  
**Date:** 2026-06-21

## Context

`franchise_specialist` via `franchise_team_labels()` on `Teams.franchID`; attr `franchise_teams` JSON array; live gate `bb-franchise-01`. Shares `product_common` with M11.

**Show-stoppers:** None for M13 / 2280.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **637** smoke passed |
| Franchise smokes | **1** passed |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Product specialist pattern | Pass |
| BRO + LAN labels for `franchID=LAD` | Pass — smoke + anchor JSON |
| Provenance `lahman.teamID`, `lahman.franchID` | Pass |
| `bb-franchise-01` exact JSON match | Pass |
| Registry team rows unchanged | Pass — read-only aggregation |
| `TeamsFranchises` table | Deferred — v1 uses `Teams` only (documented in output) |

## Design critique

**Strong:** Reusing `product_common` for M11+M12 avoids duplicate graph plumbing. Sorted distinct `Teams.name` per `franchID` matches fan-facing franchise question. Live anchor discovered on real root (8 labels).

**Sub-optimal:** Same as M11 — product shell is callback-based, not a `ProductTeamSpecialist` class yet (Paul’s class preference — follow-on after M14 or with product base class slice).

## Polish nits

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | `TeamsFranchises` metadata unused (franchise display names) | Optional enrichment slice — not required for v1 |
| N2 | `test_live_gate_runner_unit` omits `roster` / `franchise` phases | `2350` gate unit polish |

## Diff reviewed

- `franchise_specialist.py`, `product_common.py`, `categories.json`
- `tests/test_baseball_franchise_specialist.py`
- `tests/live/catalogs/baseball.yaml`, anchors, `gate_runner.py`

## For Paul (batch M10–M12)

- **Operator:** `./bin/refresh-example-network baseball --sync-only` then `./bin/gate-live baseball --phase fielding` (and `--phase roster`, `--phase franchise`, or full gate).
- **Next Cursor slice:** `2026-06-20-2260-baseball-full-warehouse-ingest-m13.md` (then `2280`, then `2340` M14, then `2350` polish).
- **Commit:** single batch commit recommended (see M10 review folder for message).
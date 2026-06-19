# Review — baseball M2 polish (M2a + M2b + M2c nits)

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **572** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` | **11** scenarios passed |

## Delivery

All A1–C3 nits from polish prompt implemented. Grok supplemented hand-test doc with **M2 extended gate (#0–#7)** and **sticky specialist cache** operator notes (post-review).

## Spec compliance

| Nit group | Result |
|-----------|--------|
| M2a A1–A3 | Pass |
| M2b B1–B4 | Pass |
| M2c C1–C3 | Pass |

## Design critique

**Strong:** `specialist_loader.py` removes duplication; full `parameters` on warehouse writes; multi-attr test + smoke close the hand-test loop; manifest/MCP surfacing polish is minimal and correct.

**Post-review doc:** Extended gate table captures Paul’s live Lahman session (including cache-clear lesson).

## For Paul

- **Commit message:** `polish(baseball): M2 warehouse manifest and resolver nits`
- **Hand-test doc** now has committed M2 extended gate — use that instead of chat-only #1–#7.
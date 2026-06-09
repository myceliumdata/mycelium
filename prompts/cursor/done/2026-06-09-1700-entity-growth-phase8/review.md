# Review: Seed from queries & network growth — Slice 8

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved**

---

## Spec coverage

| Item | Status |
|------|--------|
| Registry `attr_sources` + `last_researched_at` on `RegistryEntity` (Q8a) | Pass |
| `record_research_attribution()` after successful research pass | Pass |
| Attribution only for registry-grown entities (seed-only skips) | Pass |
| `invoke_specialists_node` applies growth attribution | Pass |
| Paul Murphy arc: unknown → bind → validate → email → re-query | Pass |
| Registry row has attribution after email research | Pass |
| Andrea Kalmans (seed) unchanged; single registry row | Pass |
| `describe_network` `policy.entity_growth` | Pass |
| CRM README growth model documented | Pass |
| Q8b–Q8d deferred (not implemented) | Pass |

## Tests

- `test_entity_growth.py`: 2/2 smoke (+ 1 unit)
- Full smoke: **212 passed**

## Non-blocking (polish post–8)

- **P12** — `output.md` says “Slice 9 (`1800`)”; polish prompt is **P** / `1800`, not Slice 9 (metering deferred).
- **P13** — Paul Murphy re-query smoke asserts `assembled` but not email value in `results`.
- **P14** — Attribution parses specialist `audit_log` via regex; works today but coupled to log format.

---

## Gate

**Entity protocol polish (`1800`)** unblocked — Slices 1–8 complete.
# Review: Research gate — Slice 6

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved**

---

## Spec coverage

| Item | Status |
|------|--------|
| `research_gate_allows()` — `current_id` + seed or validated registry | Pass |
| Supervisor defers `specialists_to_invoke` when gate fails | Pass |
| `validate_entity` schedules specialists post-promotion (Q6b) | Pass |
| Provisional + attrs → `found`, identity-only, gate message (Q6a) | Pass |
| No `research_gated` outcome | Pass |
| Validation failure path unchanged (Q5b takes precedence over gate) | Pass |
| Validated Murphy + email → `assembled` | Pass |
| Same-turn bind → validate → research | Pass |
| Seed Andrea Kalmans + email → `assembled` | Pass |
| Kalman unresolved + email → no invoke | Pass |
| `describe_network` `policy.research_gate` | Pass |
| P8/P9 dead-code cleanup (`registry_provisional_only`, `response_registry_provisional_identity`) | Pass |
| P9 duplicate-bind message respects validated state | Pass |

## Tests

- `test_entity_research_gate.py`: 6/6 smoke (+ 2 unit tests)
- Full smoke: **205 passed**

Left **uncommitted** until this review — correct governance.

## Non-blocking (polish post–8)

- **P2** (carry-over) — Weak specialist-invoke assertions in gate tests (`or outcome == assembled`).
- **P10** — `output.md` claims `invoke_specialists_node` gate defense; gate enforced in supervisor + `validate_entity` only (no in-node guard).

---

## Gate

**Slice 7 (`1600` boundary cleanup)** unblocked — prompt marked **READY**.
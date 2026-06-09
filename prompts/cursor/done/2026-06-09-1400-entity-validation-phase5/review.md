# Review: Core validation orchestration — Slice 5

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved**

---

## Spec coverage

| Item | Status |
|------|--------|
| `validate_entity` graph node after supervisor | Pass |
| Rule-based name/employer checks (Q5d, no Tavily/LLM) | Pass |
| `validation_contrib` rows (demographic + professional agents named) | Pass |
| Registry `promote_validated()` on pass | Pass |
| `entity_validated` identity-only outcome (Q5a) | Pass |
| Bind → validate → `assembled` same turn with attrs (Q5c) | Pass |
| Validation failure → `found` + message, stay provisional (Q5b) | Pass |
| Seed path skips validation (`validate_entity` no-op) | Pass |
| `_research_allowed()` defers specialists until validated | Pass |
| `describe_network` `policy.entity_validated` | Pass |

## Tests

- `test_entity_validation.py`: 5/5 smoke
- `test_entity_registry_bind.py`: updated for bind→validate same turn (10/10)
- Full smoke: **199 passed**

Left **uncommitted** until this review — correct governance.

## Notes

- Same-turn bind now returns **`entity_validated`** (not `entity_bound_provisional`) when MVR passes — expected per Q5c.
- Slice 6 can formalize the research gate; `_research_allowed()` already implements much of it.

## Non-blocking (polish post–8)

- **P6** — Validation rules centralized in `entity_validation.py`; specialists not invoked in validation mode (acceptable for Q5d v1; Pattern C wiring deferred).
- **P7** — Weak assertion in `test_murphy_bind_plus_email_validates_then_assembles_same_turn` (`or "entity_validated" not in outcome` is tautological when outcome is `assembled`).
- **P8** — Dead code after Slice 5: `registry_provisional_only` state field, `response_registry_provisional_identity()` (dispatch no longer calls).
- **P9** — Duplicate-bind message still says “provisional” after entity is validated (`dispatch.py`).

---

## Gate

**Slice 6 (`1500` research gate)** unblocked — prompt marked **READY**.
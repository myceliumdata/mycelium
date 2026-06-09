# Review: Entity key suggestions — fix 1005

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved**

---

## B1 — checkpoint serde

| Check | Result |
|-------|--------|
| `EntityKeySuggestion` in `_CHECKPOINT_MSGPACK_ALLOWLIST` | Pass |
| Same-thread smoke test (`Kalman` → `Kalmans`, sync checkpointer) | Pass |
| No `Blocked deserialization` / `EntityKeySuggestion` warnings in caplog | Pass |
| `entity_suggestions=[]` on non-suggest supervisor paths (P3) | Pass — bonus, not required |

`tests/test_entity_key_suggestions.py`: **7/7** smoke tests pass.

---

## Governance

Fix left **uncommitted** until this review — correct per WORKFLOW §3.

---

## Gate

**Slice 2 (`1100`)** is unblocked.
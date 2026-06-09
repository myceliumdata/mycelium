# Review: Entity key suggestions — Slice 1

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved** (fix `1005` also approved 2026-06-09).

---

## Summary

Slice 1 matches the locked spec for the primary Kalman → Kalmans path: `entity_key_unresolved`, empty `results`, scored `suggestions`, supervisor short-circuit, MCP policy, six smoke tests green.

One **blocking** gap: checkpoint serde for multi-turn agent retry on the same `thread_id`.

---

## Blocking

### B1 — `EntityKeySuggestion` missing from checkpoint allowlist — **fixed** (`1005`)

**Spec:** Confirmation contract allows same `thread_id`; caller re-queries with `suggestions[].entity_key`.

**Was:** `_CHECKPOINT_MSGPACK_ALLOWLIST` omitted `EntityKeySuggestion` → checkpoint serde warnings on thread resume.

**Fixed:** `1005` added `EntityKeySuggestion` to allowlist; smoke test `test_same_thread_retry_after_unresolved_no_serde_warning`.

---

## Non-blocking (polish post–Slice 8)

| # | Nit | Location |
|---|-----|----------|
| P1 | `output.md` says `entity_unknown` deferred to "slice 2" — should be Slice 3 | done/output.md |
| P2 | Specialist short-circuit test asserts `"invoke_specialists" not in response.debug` — weak; prefer audit_log or explicit `specialists_to_invoke` empty in graph state | tests/test_entity_key_suggestions.py |
| ~~P3~~ | ~~Clear `entity_suggestions` on non-suggest paths~~ — **fixed in `1005`** | — |

---

## Process note — commit before review

Cursor (or the local agent session) committed `d9e1083` to `main` before this review. That is **not** the intended workflow.

**Expected:** implement → `done/` + `output.md` → Grok review → fix slice if needed → **then** commit (or Paul commits after approval).

Updated in `prompts/cursor/WORKFLOW.md` §3 and §4.

---

## Approval gate

| Item | Status |
|------|--------|
| Kalman + email → unresolved, no specialists | Pass |
| Kalmans + email → normal path | Pass |
| Unknown / UUID / Kevin Zhang cases | Pass |
| MCP policy + docstrings | Pass |
| Same-thread retry serde | **Fixed** (`1005`) |
| Slice 2 (`1100`) | **Unblocked** after `1005` review |
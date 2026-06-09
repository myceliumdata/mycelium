# Review: Entity key suggestions — Slice 1

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved with fix slice** — do not queue Slice 2 until `1005` is reviewed.

---

## Summary

Slice 1 matches the locked spec for the primary Kalman → Kalmans path: `entity_key_unresolved`, empty `results`, scored `suggestions`, supervisor short-circuit, MCP policy, six smoke tests green.

One **blocking** gap: checkpoint serde for multi-turn agent retry on the same `thread_id`.

---

## Blocking

### B1 — `EntityKeySuggestion` missing from checkpoint allowlist

**Spec:** Confirmation contract allows same `thread_id`; caller re-queries with `suggestions[].entity_key`.

**Found:** `_CHECKPOINT_MSGPACK_ALLOWLIST` in `src/graphs/core.py` lists `EntityQuery`, `QueryResponse`, `SeedRecord`, `MyceliumGraphState` but not `EntityKeySuggestion`. After an unresolved query, checkpoint write/read logs:

```text
Blocked deserialization of models.state.EntityKeySuggestion - not in allowed_msgpack_modules.
```

**Risk:** Thread resume may drop or fail to restore suggestion state; primary visiting-agent loop is undertested.

**Fix slice:** `prompts/cursor/next/2026-06-09-1005-entity-key-suggestions-fix-checkpoint-serde.md`

- Add `("models.state", "EntityKeySuggestion")` to allowlist (both async and sync checkpointer paths).
- Add smoke test: same `thread_id`, `Andrea Kalman` → `entity_key_unresolved`, then `Andrea Kalmans` → not unresolved (no serde warning; assert via caplog or stderr-free run).

---

## Non-blocking (polish post–Slice 8)

| # | Nit | Location |
|---|-----|----------|
| P1 | `output.md` says `entity_unknown` deferred to "slice 2" — should be Slice 3 | done/output.md |
| P2 | Specialist short-circuit test asserts `"invoke_specialists" not in response.debug` — weak; prefer audit_log or explicit `specialists_to_invoke` empty in graph state | tests/test_entity_key_suggestions.py |
| P3 | Supervisor does not clear `entity_suggestions` on exact/none paths (rely on `entity_resolution_kind` in assemble) — harmless today; clear on non-suggest returns for checkpoint hygiene | supervisor.py |

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
| Same-thread retry serde | **Fail** → fix `1005` |
| Slice 2 (`1100`) | **Hold** until `1005` approved |
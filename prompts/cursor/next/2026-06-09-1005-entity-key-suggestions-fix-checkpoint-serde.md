# Task: Entity key suggestions — fix checkpoint serde (Slice 1 review)

> **READY** — Blocking fix from Slice 1 review. Run **before** Slice 2 (`1100`).

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`prompts/cursor/done/2026-06-09-1000-entity-key-suggestions-protocol/review.md`](../done/2026-06-09-1000-entity-key-suggestions-protocol/review.md) — issue **B1**
- [`docs/plans/entity-key-suggestions-phase1.md`](../../docs/plans/entity-key-suggestions-phase1.md)

**Depends on:** Slice 1 (`1000`) implemented.

**Blocks:** Slice 2 (`1100-entity-outcome-infrastructure`).

---

## Objective

Fix multi-turn agent retry on the same `thread_id` after `entity_key_unresolved`.

1. Add `EntityKeySuggestion` to `_CHECKPOINT_MSGPACK_ALLOWLIST` in `src/graphs/core.py` (both checkpointer setup paths).
2. Add smoke test: same `thread_id`, `Andrea Kalman` + email → `entity_key_unresolved`, then `Andrea Kalmans` + email → `outcome != entity_key_unresolved` and `suggestions == []`.
3. Optionally clear `entity_suggestions` on supervisor non-suggest paths (review P3 — only if trivial).

**Do not** start Slice 2 scope.

---

## Verification

```bash
uv run pytest tests/test_entity_key_suggestions.py -m smoke -q
uv run pytest -m smoke -q
```

No `Blocked deserialization of models.state.EntityKeySuggestion` warning on same-thread test.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **Do not git commit** until Grok + Paul review this slice (leave changes staged or uncommitted; Paul commits after approval).
- Update `review.md` in `1000` done folder: B1 → fixed.

---

## Deliverables

`prompts/cursor/done/2026-06-09-1005-entity-key-suggestions-fix-checkpoint-serde/` with `prompt.md`, `output.md`.
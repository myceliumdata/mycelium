# Entity key suggestions — fix checkpoint serde (1005)

## Summary

Fixed **B1** from Slice 1 review: `EntityKeySuggestion` is now in `_CHECKPOINT_MSGPACK_ALLOWLIST` so same-`thread_id` agent retry after `entity_key_unresolved` checkpoints cleanly.

## Changes

| File | Change |
|------|--------|
| `src/graphs/core.py` | Added `("models.state", "EntityKeySuggestion")` to allowlist (shared by async + sync checkpointers) |
| `tests/test_entity_key_suggestions.py` | `test_same_thread_retry_after_unresolved_no_serde_warning` |
| `src/agents/supervisor.py` | Clear `entity_suggestions=[]` on non-suggest paths (P3 hygiene) |
| `prompts/cursor/done/.../1000/review.md` | B1 marked fixed |

## Verification

```bash
uv run pytest tests/test_entity_key_suggestions.py -m smoke -q   # 7 passed
uv run pytest -m smoke -q                                        # 166 passed
```

Same-thread test: `Andrea Kalman` + email → `entity_key_unresolved`, then `Andrea Kalmans` + email on same `thread_id` → not unresolved, no `EntityKeySuggestion` serde warnings in caplog.

## For Grok + Paul

- Mark **1005** done in `TODO.md`; unblock **1100**.
- **Not committed** per fix-slice governance — Paul commits after review.
- Slice 2 (`1100`) may proceed once this is approved.

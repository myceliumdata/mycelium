# Task output — classify-04-propagate

## Claim

`prompts/cursor/next/2026-06-03-classify-04-propagate.md` → `in-progress/.../prompt.md`

## Summary

Classification metadata now flows from supervisor → core_data → `PersonResponse.debug` and final graph state.

| File | Change |
|------|--------|
| `core_data.py` | Forward `state.classifications` in payload; pass to response builders when non-empty |
| `responses.py` | `debug_for_query` accepts `**extra: Any` via `repr()`; builders take optional `classifications` |
| `test_core_graph.py` | `MYCELIUM_CATEGORIES_PATH` + `reset_category_tree` in fixture; assert classifications in non-core debug |

**Decision:** Use `repr()` for all debug extras so lists serialize cleanly and existing string assertions stay valid.

## Scope

Only the three files listed in the task prompt.

## Verification

### `uv run pytest -m smoke -q`

```
15 passed, 9 deselected in 0.12s
```

### `uv run pytest -m full -q -k "non_core or query_non_core"`

```
1 passed, 23 deselected in 0.07s
```

### CLI `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email`

```
classifications=[{'attribute': 'email', 'category': 'contact', 'assigned_agent': 'contact_specialist', ...}]
```

in `response.debug` (plus existing non-core message).

## Ready for slice 05

Implement `refresh_from_llm` (off-path LLM only).

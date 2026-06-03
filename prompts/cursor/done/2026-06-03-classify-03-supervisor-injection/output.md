# Task output — classify-03-supervisor-injection

## Claim

`prompts/cursor/next/2026-06-03-classify-03-supervisor-injection.md` → `in-progress/2026-06-03-classify-03-supervisor-injection/prompt.md`

## Summary

Minimal supervisor intelligence per approved plan: classify each `requested_attribute`, audit known mappings, return `classifications` on graph state. Route unchanged (`core_data`).

| File | Change |
|------|--------|
| `src/models/state.py` | `classifications: list[dict[str, Any]]` on `MyceliumGraphState` |
| `src/agents/supervisor.py` | `get_category_tree().classify()` loop; audit lines for non-unknown; `result["classifications"]` when attrs present |
| `tests/conftest.py` | `reset_category_tree` in session cleanup |
| `tests/test_supervisor_routing.py` | `test_supervisor_agent_classifies_requested_attributes`; no-classifications assert on routes test |

**Not in scope (slice 04):** `response.debug`, `core_data` propagation.

## Verification

### `uv run pytest -m smoke -q`

```
15 passed, 9 deselected in 0.23s
```

### `uv run ruff check` (scoped files)

```
All checks passed!
```

### Direct `supervisor_agent`

```
classifications [{'attribute': 'email', 'category': 'contact', ...}]
audit [..., "Supervisor: classified 'email' -> category=contact, agent=contact_specialist, confidence=0.95", ...]
```

### CLI `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email`

Query succeeds; message still "still researching email." (expected). `response.debug` does not yet include classifications (slice 04). Audit/classifications live in graph state after supervisor node (visible in Studio/LangSmith state, not in CLI JSON).

### Scope

Only the four files listed in the task prompt.

## Ready for slice 04

Propagate `classifications` through `core_data` and into `response.debug`.

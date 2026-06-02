# Output: Add trace_id and thread_id to PersonResponse

## Summary

Extended `PersonResponse` with two optional top-level correlation fields. Response builders accept them but default to `None` until follow-up tasks populate real values.

## New fields

| Field | Type | Purpose |
|-------|------|---------|
| `trace_id` | `str \| None` | LangSmith trace id for the graph run (observability / debugging) |
| `thread_id` | `str \| None` | LangGraph conversation thread id (session correlation) |

Both default to `None` so existing call sites and serialized JSON remain backward-compatible.

## Files modified

| File | Change |
|------|--------|
| `src/models/state.py` | Added `trace_id` and `thread_id` with docstrings on `PersonResponse` |
| `src/agents/responses.py` | `_make_response()` helper; all builders accept optional `trace_id` / `thread_id` |

**Out of scope (unchanged):** `routing.py`, `supervisor.py`, CLI, MCP, tests, docs, `graphs/core.py` fallback (still omits ids → `null` in JSON).

## Example serialization

```json
{
  "results": [],
  "message": "…",
  "debug": "…",
  "trace_id": "trace-abc",
  "thread_id": "thread-xyz"
}
```

## Verification

- `uv run pytest` — **8 passed**
- `uv run ruff check src tests` — clean
- Manual `PersonResponse(..., trace_id=..., thread_id=...)` round-trip — OK

## Follow-up queue

Tasks `0910`–`0980` will capture LangSmith trace id, pass ids through the graph, and update CLI/MCP/tests/docs.

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-03-0900-add-trace-id-and-thread-id-to-person-response.md`.

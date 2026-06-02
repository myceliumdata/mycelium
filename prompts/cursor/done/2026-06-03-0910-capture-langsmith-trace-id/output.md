# Output: Capture LangSmith trace_id during graph execution

## Summary

`run_query` now captures the LangSmith trace id after each graph invoke (when tracing is enabled) and exposes it via `get_last_invocation_trace_id()` for task `0920` to wire into `PersonResponse`. Response payloads are unchanged.

## Approach

1. **`capture_langsmith_trace_id()`** — calls `langsmith.run_helpers.get_current_run_tree()` and returns `str(run_tree.trace_id)` or `None`.
2. **`_invoke_core_graph()`** — wraps `graph.invoke` in `@traceable(name="mycelium_core_graph", run_type="chain")` when `LANGCHAIN_TRACING_V2` is truthy, then captures the trace id **inside** the traced function (after invoke, while the run context is still active).
3. **`_last_invocation_trace_id`** — module-level store read by `get_last_invocation_trace_id()`; cleared on `reset_core_graph()`.

When tracing is disabled, invoke runs normally and the stored trace id stays `None`.

## Requirements

| Env var | Role |
|---------|------|
| `LANGCHAIN_TRACING_V2=true` | Enables traced invoke wrapper |
| `LANGCHAIN_API_KEY` | Required for LangSmith export (capture still works locally if export fails) |
| `LANGCHAIN_PROJECT` | Optional project name |

## API added (`src/graphs/core.py`)

| Symbol | Purpose |
|--------|---------|
| `capture_langsmith_trace_id()` | Read current run tree trace id |
| `get_last_invocation_trace_id()` | Last id from most recent `run_query` |
| `reset_last_invocation_trace_id()` | Test reset |
| `_invoke_core_graph()` | Internal traced invoke |

## Files modified

- `src/graphs/core.py`
- `tests/test_trace_capture.py` (**new**)

## Verification

- `uv run pytest` — **11 passed**
- `uv run ruff check src tests` — clean
- Manual: with `LANGCHAIN_TRACING_V2=true`, trace id captured inside `@traceable` wrapper; without it, `get_last_invocation_trace_id()` is `None`

## Follow-up

Task `0920` should copy `get_last_invocation_trace_id()` and `thread_id` into `PersonResponse` fields.

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-03-0910-capture-langsmith-trace-id.md`.

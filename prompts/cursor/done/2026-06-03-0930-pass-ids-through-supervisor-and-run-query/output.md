# Output: Pass thread_id and trace_id through run_query

## Summary

Connected `run_query` to the supervisor/response plumbing from tasks 0900–0920. Callers' `thread_id` is set on initial graph state and echoed on the final `PersonResponse`. LangSmith `trace_id` is applied after invoke via `get_last_invocation_trace_id()` (capture runs at end of `_invoke_core_graph`).

## ID flow (end-to-end)

```text
run_query(thread_id=T)
  → MyceliumGraphState(invocation_thread_id=T)
  → supervisor / routing / response builders → PersonResponse.thread_id=T
  → graph.invoke completes
  → get_last_invocation_trace_id() → trace_id=R (if tracing on)
  → _finalize_response(..., thread_id=T, trace_id=R)
```

`trace_id` is merged in `run_query` after invoke because LangSmith capture happens when `_invoke_core_graph` finishes, not during individual supervisor nodes.

## Changes

### `src/graphs/core.py`
- `run_query` seeds `invocation_thread_id` on initial state.
- `_finalize_response()` sets `thread_id` and `trace_id` on the returned `PersonResponse` (idempotent when already set).
- Fallback empty response includes both IDs.

### `src/agents/supervisor.py`
- No changes — already reads `invocation_thread_id` / `invocation_trace_id` from state (0920).

## Verification

- `uv run pytest` — **11 passed**
- `uv run ruff check src tests` — clean
- Lookup with custom `thread_id` returns it on `PersonResponse.thread_id`; `trace_id` is `None` when `LANGCHAIN_TRACING_V2` is off.

## Follow-up

- **0940** — CLI `--thread-id` already exists; responses now populate fields.
- **0950** — MCP JSON includes new fields automatically via `model_dump_json`.
- **0960** — tests should assert `thread_id` / `trace_id` behavior.

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-03-0930-pass-ids-through-supervisor-and-run-query.md`.

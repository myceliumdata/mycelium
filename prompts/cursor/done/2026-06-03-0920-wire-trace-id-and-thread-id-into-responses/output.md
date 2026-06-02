# Output: Wire trace_id and thread_id into response construction

## Summary

Plumbed `trace_id` and `thread_id` from graph state through routing into every `PersonResponse` built by the supervisor path. Response builders already accepted these fields (task 0900); this task connects them end-to-end inside the agent layer.

## ID flow

```text
MyceliumGraphState.invocation_thread_id / invocation_trace_id
    → supervisor_agent → evaluate_supervisor_turn
    → response_* builders → PersonResponse.thread_id / trace_id
```

For **ingest** (`route_enrich`), IDs are written back onto graph state so the post-validation supervisor turn still has them.

Population of state fields from `run_query` is task **0930** (still `None` from callers today).

## Changes

### `src/agents/routing.py`
- `SupervisorDecision` gains `thread_id`, `trace_id`.
- `evaluate_supervisor_turn(..., thread_id=, trace_id=)` resolves IDs from parameters or state.
- All `response_*` calls receive `**id_kwargs`.

### `src/agents/supervisor.py`
- Passes `current.invocation_thread_id` / `invocation_trace_id` into `evaluate_supervisor_turn`.
- `_apply_decision` persists IDs on state when routing to enrich.

### `src/models/state.py` (minimal addition for ingest round-trip)
- `invocation_thread_id`, `invocation_trace_id` on `MyceliumGraphState`.

Required so LangGraph can carry IDs across enrich → validator → supervisor; not listed in the strict file list but necessary for plumbing.

### `src/agents/responses.py`
- No code changes (already wired in 0900).

## Verification

- `uv run pytest` — **11 passed**
- `uv run ruff check src tests` — clean

## Follow-up

- **0930** — set `invocation_*` on initial state from `run_query` + `get_last_invocation_trace_id()`.
- **0940+** — CLI/MCP/tests/docs.

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-03-0920-wire-trace-id-and-thread-id-into-responses.md`.

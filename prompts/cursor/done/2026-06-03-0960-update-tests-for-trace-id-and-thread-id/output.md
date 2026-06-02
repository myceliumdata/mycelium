# Output: Update Tests for trace_id and thread_id

## Summary

Extended graph integration tests to assert `thread_id` and `trace_id` on `PersonResponse` from `run_query`, covering lookup, ingest, defaults, and traced capture.

## Changes

### `tests/test_core_graph.py`

| Test | Assertions |
|------|------------|
| `test_run_query_echoes_thread_id_on_lookup` | Explicit `thread_id`; `trace_id` is `None` without tracing |
| `test_run_query_echoes_thread_id_on_ingest` | Same on successful ingest path |
| `test_run_query_default_thread_id` | Default `thread_id="default"` when omitted |

### `tests/test_trace_capture.py`

| Test | Assertions |
|------|------------|
| `test_run_query_clears_trace_id_when_tracing_disabled` | Extended to assert `response.thread_id` and `response.trace_id is None` |
| `test_run_query_sets_trace_id_on_response_when_captured` | Patches tracing + capture; expects `trace_id == "trace-abc"` on response |

## Verification

- `uv run pytest` — **15 passed**
- `uv run ruff check tests` — clean

## Open questions

None.

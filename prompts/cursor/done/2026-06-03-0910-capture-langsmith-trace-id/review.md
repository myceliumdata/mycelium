# Review — 2026-06-03-0910-capture-langsmith-trace-id

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Excellent, narrowly-scoped capture implementation. Cursor correctly applied LangSmith's `get_current_run_tree()` + conditional `@traceable` wrapper to make the invocation's trace_id available immediately after `graph.invoke`, exposed it via a simple getter, maintained full backward compatibility when tracing is off, and delivered solid verification including a real end-to-end capture with a live trace UUID.

## Strengths

- **Strict scope adherence**: Only `src/graphs/core.py` was modified and `tests/test_trace_capture.py` was added. No changes to response builders, routing, supervisor, CLI, MCP, docs, or `MyceliumGraphState`. The in-progress marker was cleaned up exactly as specified. Historical `done/` files untouched.

- **Correct and elegant capture technique**:
  - `_invoke_core_graph` clears the stored id, then (only when `LANGCHAIN_TRACING_V2` is truthy) wraps the invoke in a `@traceable(name="mycelium_core_graph", run_type="chain")`.
  - Inside that traced wrapper, after `graph.invoke(...)` returns but while the run context is still active, it calls `capture_langsmith_trace_id()` and stores the result.
  - `capture_langsmith_trace_id()` does a lazy import of `langsmith.run_helpers.get_current_run_tree`, safely returns `None` on any failure path (no langsmith, no current tree, disabled tracing).

- **API and lifecycle hygiene**:
  - `get_last_invocation_trace_id()` for downstream consumers (0920+).
  - `reset_last_invocation_trace_id()` and integration into the existing `reset_core_graph()` for test isolation (critical because of the module globals).
  - `_langsmith_tracing_enabled()` helper centralizes the env var check using the standard set of truthy values.

- **Verification**:
  - `uv run pytest` — 11 passed (existing tests + 3 new: two unit tests for the capture helper with mocks, one full `run_query` disabled-tracing integration test).
  - `uv run ruff check src tests` — clean.
  - Manual test (via python -c with `LANGCHAIN_TRACING_V2=true`, no `LANGCHAIN_API_KEY`): `run_query` succeeded and `get_last_invocation_trace_id()` returned a real trace id (e.g. `019e8674-387f-7692-9c36-ff9abc7dd93a`). The LangSmith client warning logs confirmed the same root trace id was used for the multipart ingest attempt, proving the captured id matches the actual invocation trace.

- **Clear, actionable output.md**: Documents the approach, the exact env var contract (with table), the new public symbols, requirements, and explicitly calls out the handoff to task 0920. Also notes the in-progress cleanup.

- **Defensive implementation**: Works whether or not an API key is present (id capture is a local run-tree operation; export is separate). No hard failures or required configuration beyond the standard LangSmith env vars already documented in .env.example.

## Minor Observations

- Automated test coverage for the *enabled* tracing path is intentionally light (unit tests mock the run tree; the integration test forces the disabled branch via `monkeypatch.delenv`). This matches the incremental nature of the series — 0960 will have the opportunity to add richer tests once the ids are wired into responses and surfaced in CLI/MCP. The manual verification performed by Cursor (and re-confirmed here) was sufficient and convincing for this slice.

- When tracing is enabled, every `run_query` now creates an additional top-level "mycelium_core_graph" span that wraps the LangGraph execution. The actual supervisor/enrich/validator nodes become children under the same trace (visible in the trace id prefixes in the auth error log during manual test). This is the intended side-effect of the wrapper and gives external callers a stable, named trace root to correlate against. Acceptable and even useful.

- Capture is performed *after* the inner `graph.invoke` completes. This is correct for obtaining the trace id of the overall invocation (demonstrated by the matching UUID).

- As designed, this task leaves `run_query`'s fallback `PersonResponse(...)` and the `final.response` coming out of graph state without `trace_id`/`thread_id` populated. Those will be wired in 0920–0930 using the new getter + the `thread_id` parameter already available on `run_query`.

- `thread_id` itself is not "captured" here (it is an input); the task title and scope correctly focused only on the LangSmith trace_id.

- The new test follows existing project patterns (storage/core_identity/graph resets, monkeypatch for paths, temp seed files).

## Verdict

**Strongly Approved.**

This is exactly the kind of small, mechanical, high-signal increment the workflow is designed for. The implementation is production-resilient, the verification (especially the live trace capture without an API key) gives high confidence, and the handoff documentation is precise. No scope creep, no behavior change for callers when tracing is off, and the singleton/global pattern is consistent with the rest of `graphs/core.py`.

**Status:** Approved. No changes requested.

Ready for the next task in the series: `prompts/cursor/next/2026-06-03-0920-wire-trace-id-and-thread-id-into-responses.md`. Once wired, subsequent tasks will surface the values in CLI output, MCP, update tests, and docs. The foundation for long-running external agent conversations and production debugging is now in place at the graph execution layer.
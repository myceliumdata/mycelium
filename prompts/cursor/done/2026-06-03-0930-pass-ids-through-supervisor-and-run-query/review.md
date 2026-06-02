# Review — 2026-06-03-0930-pass-ids-through-supervisor-and-run-query

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Excellent completion of the core plumbing. This task bridges the gap between the internal agent-layer wiring (0920) and the public `run_query` entry point, ensuring caller-supplied `thread_id` and post-invoke LangSmith `trace_id` reliably reach the `PersonResponse`. Changes are minimal, focused, and correctly timed (thread on entry, trace after capture).

## Strengths

- **Precise end-to-end connection**:
  - `run_query` now seeds `invocation_thread_id` on the initial `MyceliumGraphState` (so the 0920 supervisor/routing machinery sees it and propagates it into builders).
  - After `_invoke_core_graph` (where capture happens inside the traceable wrapper), it pulls `get_last_invocation_trace_id()`.
  - `_finalize_response` helper then ensures both IDs are on the outbound response (for the normal `final.response` path) or the fallback `PersonResponse`.

- **Smart post-processing for trace timing**:
  - Correctly recognizes that LangSmith trace capture occurs *after* `graph.invoke` returns (inside `_invoke_core_graph`), so it cannot be known during supervisor turns.
  - The `_finalize_response` is idempotent (early return if values already match) and uses `model_copy(update=...)` — clean Pydantic usage that avoids mutating the original object from the graph state.

- **Fallback also updated**:
  - The "Graph finished without a response payload" case now carries the caller's `thread_id` and any captured `trace_id`. Previously it would have dropped them; now consistent.

- **Supervisor untouched**:
  - As documented in the output, no changes needed here (0920 had already made `supervisor_agent` and `_apply_decision` read from state and write IDs back for the enrich round-trip). This task respected the layering.

- **Verification quality**:
  - `uv run pytest` — 11 passed.
  - `uv run ruff check src tests` — clean.
  - Manual checks in output (and re-confirmed here): custom `thread_id` is echoed; when `LANGCHAIN_TRACING_V2=true` a real trace UUID appears on `response.trace_id` (matching the internal capture); disabled case remains `None`.
  - In-progress marker correctly cleaned.

- **Clear documentation**:
  - Output.md includes a concise ASCII flow, explains the "why after invoke" for trace, lists exact changes, and gives precise follow-ups (0940 CLI surfacing, 0950 MCP, 0960 tests).

## Minor Observations

- The `invocation_trace_id` field on `MyceliumGraphState` is never seeded by `run_query` (intentionally, since capture is post-invoke). During graph execution it will be `None`, so builders see `None` for trace, and `_finalize_response` always supplies the real value (or `None`). This works correctly for both lookup and ingest paths, but it means the state field for trace is mostly a "pass-through for the enrich loop" that stays `None` until finalize. Acceptable internal detail.

- `_finalize_response` always runs on the success path, even when the IDs inside `final.response` (set by 0920 builders from state) already match the run_query values. The early `if` guard prevents unnecessary copies, which is good.

- No changes to `MyceliumGraphState` itself in this task (the fields were added in 0920). `run_query` only populates the thread one on entry.

- Scope was strictly followed: only `src/graphs/core.py` + the done/ artifacts. CLI arg handling (already partially present in main.py from prior work), MCP, tests, and docs left for later tasks.

- Current tests (esp. `test_core_graph.py`) do not yet assert on `response.thread_id` or `response.trace_id` — they will continue to pass (they get "default" + None). This is correct per the "out of scope" note; 0960 will add the assertions.

- When tracing is enabled without an API key, the warning + auth error still appears (as before), but the `trace_id` is captured and surfaced on the response. This is the intended "local capture works even if upload fails" behavior.

## Verdict

**Strongly Approved.**

This task does exactly what it set out to: makes `run_query` the single place that owns the caller `thread_id` and the captured `trace_id`, and guarantees they appear on every `PersonResponse` (success or fallback). The helper is a nice touch for cleanliness. The series is now at the point where the IDs are *actually returned* from the public API.

**Status:** Approved. No changes requested. Ready for Cursor to process the next task (`2026-06-03-0940-update-cli-to-support-thread-id-and-ids-in-response.md`).

(The uncommitted items in the working tree — prior review.md files, the TODO observability note, architecture naming tweak, and test param rename — remain unrelated to this increment.)
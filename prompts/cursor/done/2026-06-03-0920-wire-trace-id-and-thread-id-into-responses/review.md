# Review — 2026-06-03-0920-wire-trace-id-and-thread-id-into-responses

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Solid, focused plumbing task. Cursor connected the dots between the capture mechanism (0910), the already-updated response builders (0900), and the supervisor/routing layer so that `thread_id` and `trace_id` flow into every `PersonResponse` constructed during a graph turn. The changes correctly handle the multi-turn ingest path by propagating the IDs through LangGraph state.

## Strengths

- **Clear ID flow design**: 
  - Added `invocation_thread_id` / `invocation_trace_id` to `MyceliumGraphState` (internal only).
  - `SupervisorDecision` now carries `thread_id`/`trace_id`.
  - A small `_resolve_invocation_ids` helper prefers explicit parameters over state values.
  - All `response_*` builders are called with `**id_kwargs`.
  - In the `route_enrich` case, `_apply_decision` writes the IDs back onto the state payload so they survive the enrich → validator → supervisor round-trip and are available for the final response.

- **Minimal and correct changes to supervisor**:
  - `supervisor_agent` now passes the IDs from state into `evaluate_supervisor_turn`.
  - For final responses, the IDs live inside the `PersonResponse` (via the builders); only the enrich routing path needs to echo them at the state level.
  - Updated the module docstring to document the propagation responsibility.

- **Scope adherence with honest exception**:
  - Core work was exactly in `routing.py` and `supervisor.py` (plus the pre-wired `responses.py` left untouched).
  - The addition to `state.py` (two new optional fields on `MyceliumGraphState`) was outside the strict prompt list, but Cursor clearly documented it in `output.md` as a "minimal addition for ingest round-trip" required for LangGraph to carry the values across nodes. This was the right engineering call.

- **No behavior change when IDs are absent**: All new fields default to `None`. Existing response shapes, messages, and debug content are unchanged. Current callers (including tests and the still-unwired `run_query`) continue to see `trace_id=None` / `thread_id=None`.

- **Verification**:
  - `uv run pytest` — 11 passed (no regressions in core graph or routing tests).
  - `uv run ruff check src tests` — clean.
  - In-progress marker cleaned up correctly.

- **Excellent handoff documentation**: `output.md` includes a compact flow diagram, a clear "Changes" breakdown by file, explicit "responses.py — no changes (already wired)", and precise follow-up pointers to 0930 (population in `run_query` + initial state) and later tasks.

## Minor Observations

- The `SupervisorDecision` now duplicates the IDs (once on the dataclass, once inside `decision.response` for respond cases). This is harmless and necessary for the enrich case where `response` is `None`. Acceptable for internal coordinator state.

- The core_identity parameter rename (`identity=` → `core_identity=`) showed up in the routing diff. This was consistency follow-up from the earlier rename task; the on-disk tests were already (or became) updated to match.

- `MyceliumGraphState` grew two more fields. (User has previously expressed uncertainty about the role of graph state; this addition is narrowly for correlation ID propagation and stays internal.)

- The fallback `PersonResponse(...)` in `src/graphs/core.py:171` and any direct constructions still produce `None` for the new fields. This is expected — 0930 will address population at the `run_query` boundary (and should also update the fallback and any test fixtures).

- Routing tests exercise the decision paths but do not yet assert on `decision.thread_id` / `decision.trace_id` or the IDs inside responses (correctly left for task 0960).

- No CLI or MCP changes (per strict scope). Those will surface the now-populated values.

## Verdict

**Strongly Approved.**

This is exactly the kind of narrow, reviewable plumbing increment the workflow is meant for. Cursor made the internal agent layer ready to carry the observability IDs, handled the tricky LangGraph round-trip for ingest correctly, added a helpful resolver helper, and left a crystal-clear audit trail in the output artifact.

The wiring inside the supervisor/coordinator is now complete for this slice. The next step (0930) can focus purely on getting the values from `run_query` (thread_id param + `get_last_invocation_trace_id()`) onto the initial state so they actually appear in real responses.

**Status:** Approved. No changes requested. Ready for Cursor to pick up `2026-06-03-0930-pass-ids-through-supervisor-and-run-query.md`.

(The uncommitted workspace changes — TODO note on post-series LangSmith config, architecture wording, and test param rename — are separate and unrelated to this task.)
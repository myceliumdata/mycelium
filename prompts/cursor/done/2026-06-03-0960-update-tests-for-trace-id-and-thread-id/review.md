# Review — 2026-06-03-0960-update-tests-for-trace-id-and-thread-id

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Thorough and well-scoped test updates. Added dedicated assertions for the new `thread_id` / `trace_id` fields across lookup, ingest, default generation, and the traced capture path. Tests correctly use explicit `thread_id` in calls, assert the echo, and handle `trace_id=None` in non-tracing envs while using patches for the positive capture case. No behavior changes to existing tests.

## Strengths

- **Good coverage of the main paths** (in `test_core_graph.py`):
  - `test_run_query_echoes_thread_id_on_lookup` — explicit thread_id, expects `trace_id is None`.
  - `test_run_query_echoes_thread_id_on_ingest` — same on successful provided_data ingest path + checks the "Added" message.
  - `test_run_query_default_thread_id` — verifies the `run_query` default of `"default"` (when no thread_id passed) and `trace_id is None`.

- **Proper extension of the capture test** (in `test_trace_capture.py`):
  - Updated the "tracing disabled" test to also call with explicit thread_id and assert both fields on the *response* (not just the module getter).
  - New `test_run_query_sets_trace_id_on_response_when_captured` — uses `monkeypatch` for env + `patch` on `_langsmith_tracing_enabled` and `capture_langsmith_trace_id` to simulate capture without needing a real LangSmith key or side effects. Asserts the exact trace_id bubbles up to `response.trace_id`.

- **Follows project patterns**:
  - Uses the same temp_storage fixture / reset dance as surrounding tests.
  - For the traced test, follows the style of the existing disabled test (tmp_path + monkeypatch for paths + env).
  - Assertions are precise and minimal.

- **Verification**:
  - At task time: 15 passed (overall suite grew as expected).
  - Ruff clean.
  - The patches isolate the capture logic nicely, so the test doesn't depend on the full traceable wrapper executing.

- **Scope**: Only touched test files (`test_core_graph.py`, `test_trace_capture.py`). No production code changes. Perfect.

## Minor Observations

- The default thread_id test asserts exactly `"default"`. This matches the current `run_query(..., thread_id: str = "default")` signature. If the default ever changes (e.g. to a generated UUID like the CLI does), this test will need updating — but that's fine; it's testing the current contract.

- No assertions yet on the *content* of `trace_id` in the non-patched paths beyond `is None`. That's appropriate because without the env/patches, capture is disabled.

- The new traced test sets `LANGCHAIN_TRACING_V2` via monkeypatch but then also patches `_langsmith_tracing_enabled` to return True. This is defensive and ensures the test works even if the env var check logic evolves slightly.

- No MCP-specific tests added (out of scope for this task; the MCP layer was updated in 0950 but its integration tests can be a later addition if desired).

- Suite size increased; later 0980 added even more (test_langsmith_utils), bringing us to 19 total — all still green.

## Verdict

**Strongly Approved.**

Excellent incremental test work. The assertions directly validate the end-to-end promise of the 09xx series: when you pass a `thread_id` to `run_query`, it comes back on the response; when tracing capture succeeds, the `trace_id` appears on the response too. The use of patches for the positive tracing case is clean and reliable.

No issues. These tests will catch regressions in the core plumbing.

**Status:** Approved. No changes requested. Ready for documentation (0970) and the optional polish (0980).
# Review: 2026-06-05-1080-cleanup-tests

**Status:** Approved.

## What was done
- Confirmed that the major ingest test deletions (`test_ingest_new_person`, `test_ingest_validation_failure`, `test_run_query_echoes_thread_id_on_ingest`, etc.) were already handled in the 1000-1050 batch.
- This task focused on expanding and verifying query-only coverage:
  - Added `test_graph_invokes_supervisor_then_core_data` in test_core_graph.py to assert the post-1070 graph flow (supervisor routes to core_data, audit logs show both).
  - Added `test_routing_non_core_attributes` and updated not-found test in test_supervisor_routing.py to assert no "ingest" or "provided_data" language.
  - Added `test_supervisor_agent_routes_to_core_data` (verifies thin supervisor: sets route, no response built here).
  - Added `test_core_data_agent_non_core` in the agent's test file.
- Updated docstrings to reflect query-only scope.
- Ran full pytest (22 passed) and ruff (clean).
- Output includes clear notes on tests to re-add when data addition returns (public ingest, enrich/validator, etc.).

## Code quality
- Tests are well-targeted: cover the new supervisor → core_data routing, thin supervisor behavior (no response in supervisor output), non-core, and end-to-end via ainvoke.
- The graph test directly exercises `build_core_graph` + `ainvoke`, which is appropriate for validating the simplified graph.
- Negative asserts ensure no leftover ingest references in responses.
- Good that it reuses the stub pattern from prior agent tests.
- Matches the prompt: deletions not re-done (already done), added coverage for core_data_agent as recommended, verified pytest.

## Issues / Notes
- None. The output accurately notes that ingest removals were prior, and this expands coverage.
- The supervisor_routing test still exercises `evaluate_supervisor_turn` directly (now mostly for tests, as main path uses core_data_agent), which is fine and preserves the logic.
- 22 tests now, up from previous (good expansion).
- Follow-ups correctly identified for when ingest is re-added internally.

**Recommendation:** Approve. Tests are now properly aligned with the query-only public interface and core_data_agent architecture.

Reviewed by Grok.

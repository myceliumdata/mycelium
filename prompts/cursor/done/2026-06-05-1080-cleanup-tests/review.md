# Review: 2026-06-05-1080-cleanup-tests

**Status:** Approved.

## What was done
- Confirmed that ingest tests were already removed in the 1000–1050 batch commit (be1d5ec).
- Expanded test coverage for the query-only world:
  - Added `test_graph_invokes_supervisor_then_core_data` in `test_core_graph.py` to verify the new graph path (supervisor → core_data) via direct `ainvoke`, checking audit logs for routing.
  - Added `test_routing_non_core_attributes` and `test_supervisor_agent_routes_to_core_data` in `test_supervisor_routing.py`.
  - Added `test_core_data_agent_non_core` in `test_core_data_agent.py`.
- Updated module docstrings.
- Removed/updated asserts and tests that referenced ingest (e.g., no more "ingest_required", no provided_data in not-found messages).
- Ran pytest (22 passed) and ruff (clean).
- Output notes tests to re-add later when internal data addition returns.

## Code quality
- Tests are appropriate and cover the new architecture: thin supervisor routing to core_data_agent, query responses, non-core handling.
- The end-to-end graph test using `build_core_graph` + `ainvoke` is a good way to validate the flow without relying on the old evaluate_supervisor_turn.
- Negative assertions ensure no bleed from removed ingest paths.
- Followed the prompt: did not re-do the deletions (already done), added coverage for core_data_agent as suggested.
- Test file now documents "query-only public paths".

## Issues / Notes
- None. The task output accurately reflects that ingest removal was prior, and this task focused on expansion and verification.
- Good that it mentions follow-ups for when ingest returns (e.g., public ingest tests, enrich/validator, etc.).
- The supervisor_routing test still tests `evaluate_supervisor_turn` (which is now test-only, as the main path uses core_data_agent), which is fine for now.

**Recommendation:** Approve. Tests are now aligned with the query-only + core_data_agent design.

Reviewed by Grok.

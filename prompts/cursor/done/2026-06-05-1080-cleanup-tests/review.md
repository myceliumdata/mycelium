# Review: 2026-06-05-1080-cleanup-tests

**Status:** Approved.

## What was done
- Confirmed ingest tests were already removed in prior 1000-1050 batch.
- Expanded coverage:
  - Added `test_graph_invokes_supervisor_then_core_data` in test_core_graph.py (verifies post-1070 flow via ainvoke, audit logs show supervisor routing + CoreDataAgent).
  - Added `test_routing_non_core_attributes`, updated not-found test in test_supervisor_routing.py (asserts no ingest language).
  - Added `test_supervisor_agent_routes_to_core_data` (thin supervisor: sets route, no response built).
  - Added `test_core_data_agent_non_core` in agent's test.
- Updated docstrings to query-only.
- Ran pytest (22 passed), ruff clean.
- Output notes re-add tests for future internal ingest.

## Code quality
- Tests target the new architecture well: graph path, thin supervisor (no response in its output), non-core, core_data non-core.
- Direct ainvoke test is good for validating simplified graph.
- Negative asserts ensure no leftover ingest references.
- Matches prompt: deletions not re-done (already prior), added core_data tests as recommended, verified full suite.
- 22 tests (expansion good).

## Issues / Notes
- None. Output accurately describes prior removals and new additions.
- routing test still covers evaluate_supervisor_turn (test-only now), fine.
- Good notes on re-adding for future.

**Recommendation:** Approve. Tests aligned with query-only + core_data_agent.

Reviewed by Grok.

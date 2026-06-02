# Review: 2026-06-05-1070-simplify-graph-remove-ingest-nodes

**Status:** Approved.

## What was done
- Simplified `src/graphs/core.py` to query-only graph: supervisor + core_data_agent.
- Removed enrich/validator nodes, the ingest loop edges, and their imports.
- Updated `_route_after_supervisor` to check for "core_data".
- Added `core_data` node and edge core_data -> END.
- Updated docstrings in graph, run_query, etc.
- The commit also cleaned up supervisor.py (now ultra-thin router that just sets route="core_data") and state.py (route literal to "core_data").
- Output.md has clear before/after table, example of supervisor output, verification.

## Code quality
- Graph structure now matches the objective: START → supervisor (classify & route) → core_data (lookup & response) → END.
- Supervisor is thin coordinator: just sets the route based on classification (no more inline logic or to_thread here; logic is in core_data_agent).
- Matches the "supervisor produce a decision that leads to core_data node".
- Old enrich/validator left on disk but unwired (as planned for re-adding ingest later).
- The additional changes to supervisor and state were necessary to complete the simplification consistently (even though prompt focused on graphs/core.py, the output accurately reflects the state after the commit).
- core_data_agent (from 1060) is now used in the main graph path.

## Verification
- From output: pytest and ruff passed.
- From my checks: graph nodes are supervisor + core_data (no enrich/validator in active graph).
- run_query for existing person succeeds (from prior test runs).
- Route is now "core_data".

## Issues / Notes
- None major. The duplication of lookup logic (in routing.py for tests vs core_data_agent) is acceptable for now; routing.evaluate_supervisor_turn is now primarily test-only.
- __init__.py still exports old agents (deferred to 1100 as noted).
- Docs were updated in parallel 1090 task, which references the pending wiring.
- Good note in output about follow-ups for tests and 1100.

**Recommendation:** Approve. This successfully removes the public ingest path from the graph and wires the proper core data agent.

**Follow-up:** Task 1100 for agents/__init__.py, and ensure tests/docs reflect the new nodes (e.g. expect "core_data" in traces).

Reviewed by Grok.

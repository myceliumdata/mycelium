# Task: Wire the core_data_agent into the graph and clean agents/__init__.py (and any remaining ingest wiring)

## Objective
Complete the graph simplification by actually adding the `core_data_agent` node (from the earlier creation task) and updating the supervisor's routing decision so that queries flow through the new specialist. Also clean `src/agents/__init__.py` and remove any leftover imports/re-exports of the now-unwired enrich/validator agents.

## Constraints
- The final active graph for the public query interface should be supervisor (classify & coordinate) + core_data (perform core lookup & response) .
- Keep the supervisor thin.
- Remove enrich and validator from the active graph and from the public __init__ exports.
- The old enrich/validator files may stay on disk for the "add back later" work; just stop importing and wiring them.
- All query behavior must continue to work.

## Exact Steps
1. Edit `src/graphs/core.py` (if not fully done in the simplify-graph task):
   - Add `from agents.core_data import core_data_agent`
   - In build: `graph.add_node("core_data", core_data_agent)`
   - Set up the conditional (or direct edge) after supervisor so that core lookups go to the core_data node.
   - Remove any remaining references to enrich/validator nodes/edges/imports.
   - Update the _route_after_supervisor logic (or replace it) to produce a route that leads to core_data for normal queries.
   - Keep the async checkpointer etc.
2. Edit `src/agents/__init__.py`:
   - Remove enrich_agent and validator_agent.
   - Add `from agents.core_data import core_data_agent`
   - Export `core_data_agent` and `supervisor_agent`.
3. If the supervisor or routing still contains any "route_enrich" or ingest decision code, finish removing it here (coordinate with the simplify-routing and update-supervisor tasks).
4. Verify that `get_core_graph()` builds without error and a query can still be executed via `run_query`.
5. Do not touch tests or docs (those have their own tasks).

## Required Output
- Diffs showing the new node wiring and the cleaned __init__.
- Smoke test that a query still succeeds end-to-end.
- Note that the graph is now query-only with the proper core data agent.

Claim via the standard next/ → in-progress move. Clean only your file from in-progress when done.

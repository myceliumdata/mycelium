# Task: Simplify the core graph — remove ingest nodes and wire the new core data agent (query-only)

## Objective
Update `src/graphs/core.py` so the compiled graph no longer contains the enrich/validator loop (those were purely for the removed public ingest path). The graph should become a simple query path that uses the new `core_data_agent` (created in the previous task in this series) as the specialist that owns core data lookups.

After this task the graph structure should be approximately: START → supervisor (classify) → core_data (perform lookup + build response) → END. The supervisor stays thin and only decides routing.

## Constraints & Principles
- Supervisor is the coordinator/router.
- Core data management is now owned by its own proper agent node.
- No more support for adding data in the graph for the public path (internal coordination later).
- Keep the async checkpointer and all existing query/trace/thread behavior.
- Remove or comment the old enrich/validator imports and nodes.
- Update `_route_after_supervisor` (or replace the conditional) to route to the core_data node for lookups.
- The build function and get_core_graph must still work for pure queries.

## Context
- Current graph (before this task) still wires supervisor + enrich + validator with the conditional for "enrich".
- The new core_data_agent (from prior task) is the replacement specialist for core lookups.
- In the supervisor task (parallel or prior), the routing logic will have been simplified to produce decisions that can be turned into a route to "core_data".
- This task focuses on the graph wiring and removal of the old ingest loop.

## Exact Steps
1. Edit `src/graphs/core.py`:
   - Remove imports for enrich_agent and validator_agent.
   - In build_core_graph: remove the two add_node calls for enrich/validator.
   - Remove the add_edge calls that created the ingest loop.
   - Update the conditional edges: instead of routing on "enrich", have the supervisor produce a decision that leads to a "core_data" node (or always route queries to core_data after supervisor).
   - Add the core_data node: `graph.add_node("core_data", core_data_agent)`
   - Update `_route_after_supervisor` or introduce a new router that decides "core_data" vs "__end__" based on the simplified supervisor output.
   - Keep the START → supervisor edge.
   - Update the module docstring and build docstring to reflect "query-only graph using supervisor + core_data_agent".
   - Keep all the async checkpointer, traceable wrapper, run_query, etc. unchanged.
2. Import the new core_data_agent (from agents.core_data).
3. Make sure `get_core_graph()` still returns a usable graph for queries.
4. Do not touch tests, CLI, MCP, or docs in this task (separate).

## Required Output
- Diff and explanation in the done/ output.md.
- Confirmation that a query still runs end-to-end via the new structure (you may run a quick python smoke test).
- Notes about what the supervisor must now output to reach the core_data node.

Claim by moving to in-progress/ first. Only clean your own file from in-progress on completion.

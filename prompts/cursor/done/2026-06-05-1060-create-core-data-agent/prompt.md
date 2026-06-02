# Task: Create a proper CoreDataAgent as a graph node for managing core data (query path)

## Objective
Introduce a new proper LangGraph agent node `core_data_agent` that encapsulates all core data management (starting with lookups). This replaces the current inline calls through the CoreIdentity facade from inside the supervisor/routing logic. The supervisor will (in a follow-up task) route core lookup work to this specialist agent.

For this task, implement the agent for the query/lookup case only (find_by_key). Persist/ingest support will be re-added later as an internal coordination concern.

## Constraints & Principles (from architecture.md)
- Supervisor must be a thin coordinator/router — it must not contain core data logic.
- A dedicated specialist ("proper agent") must own core person identity data.
- The new agent must follow the same pattern as the existing ones: async def xxx_agent(state: MyceliumGraphState | dict) -> dict[str, Any] that returns small state deltas.
- Use the existing CoreIdentity (or directly the storage facade) internally for now; the goal is to give core data its own explicit node in the graph.
- The agent should set person, response, audit_log, etc. on the state.
- Keep the implementation minimal and focused on lookup for the query-only public interface.
- Name the module `src/agents/core_data.py` and the function `core_data_agent`.
- Update the class docstring in the old core_identity.py if you touch it, but prefer to leave the facade in place for this task (the agent will use get_core_identity()).

## Context
- Currently `evaluate_supervisor_turn` (in routing) does the CoreIdentity.find_by_key call directly while building the decision.
- We want the supervisor to hand off to a specialist node for this work, making the architecture match "proper agent for managing core data".
- Enrich/validator were the previous examples of such routed specialist nodes (they were ingest-only and are being removed in parallel tasks).
- The new core data agent will be the permanent home for core lookup (and future core management).

## Exact Steps
1. Create new file `src/agents/core_data.py`:
   - Implement `async def core_data_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:`
   - Inside: coerce state, call get_core_identity().find_by_key(query.person_key), build the appropriate response (found / not-found / non-core) using the responses helpers, return deltas for "person", "response", "audit_log", etc.
   - Add proper module and function docstrings explaining it is the specialist agent owning core data.
   - Handle thread/trace id propagation if the state carries invocation_*_id.
   - Keep it synchronous under the hood via to_thread if needed for storage (match supervisor pattern).
2. Also edit `src/agents/core_identity.py` minimally if needed (e.g. a one-line note that it is now used by the CoreDataAgent).
3. Do **not** yet wire the agent into the graph or change supervisor/routing to route to it — that is a separate task.
4. Do **not** touch enrich/validator/person_prep (being removed in parallel).

## Required Output
- The new file.
- Artifacts in done/ including the full new file content or diff, explanation of the agent, how it will be used by supervisor later.
- Claim the task first.

Follow WORKFLOW.md claiming protocol.

# Task: Simplify routing.py for query-only paths (remove all ingest logic)

## Objective
Refactor `src/agents/routing.py` so `evaluate_supervisor_turn` only handles lookup cases (found, not-found, non-core). Completely remove the `provided_data` branch, the validation-passed ingest-success branch, and calls to ingest response builders. The function should now always perform a core lookup via CoreIdentity (or the future core data agent) and return the appropriate query response.

## Constraints & Principles
- Supervisor must remain a thin coordinator.
- All core data access still goes through CoreIdentity for now (proper agent extraction is a separate task).
- Remove any logic that assumed data could be added via the public query path.
- Keep the response builders for the three query outcomes.
- Update the module docstring.

## Context
- This function currently has the big if-ladder that includes the ingest decision points (provided_data, validation_passed + person, etc.).
- Those branches will be dead after public ingest removal.
- The supervisor agent calls this to classify.

## Exact Steps
1. Edit `src/agents/routing.py`:
   - Remove imports for ingest response functions.
   - Strip out the `if state.validation_passed is False`, the `if state.validation_passed is True and state.person`, and the `if query.provided_data is not None` branches.
   - The remaining logic should be: always do the find_by_key (unless we route to core_data agent later), then decide found vs not-found vs non-core.
   - Simplify the function: it now only ever produces a respond action for query results.
   - Clean the docstring and any comments about ingestion or routing to enrich.
   - Remove unused SupervisorDecision fields if any become dead (e.g. action="route_enrich").
2. Make sure the function still returns a valid SupervisorDecision for the three query cases.
3. Do not yet change how supervisor calls it or wire any core_data node (later tasks).

## Required Output
- Standard prompt/output/review artifacts in done/.
- Diff focused on the simplification.
- Note that this removes the last public ingest decision point in routing.

Claim the task by moving the file to in-progress/ before editing anything.

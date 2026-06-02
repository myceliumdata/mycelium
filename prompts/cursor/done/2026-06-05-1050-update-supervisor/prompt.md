# Task: Clean supervisor.py of ingest references and simplify for query-only

## Objective
Update `src/agents/supervisor.py` so the supervisor agent and its helpers no longer contain any code or log messages related to ingestion or the enrich routing path. The node should now only ever classify queries and produce responses (or delegate to the core data agent in a follow-up task).

## Constraints
- Keep the async node signature and the to_thread pattern for core data access (for now).
- Supervisor must stay thin — it coordinates, it does not do storage work itself.
- Remove the "provided_data present — routing to enrich" log path and any related _apply_decision branches.

## Exact Steps
1. Edit `src/agents/supervisor.py`:
   - Remove or simplify the branch in `_apply_decision` that handled "route_enrich".
   - Remove the log line about provided_data.
   - Update the module and function docstrings to say "coordinator and router for core lookups and specialist handoff" (remove "ingest").
   - Clean the supervisor_agent docstring.
   - The function can now be simpler: always end up calling evaluate (which will be query-only after its task) and applying a respond decision.
2. The file should still support delegation to core identity via the thread offload.
3. Leave any core_data_agent wiring for the dedicated task.

## Required Output
- Artifacts in done/ with diff and notes.
- Claim first via in-progress/ move.

See WORKFLOW.md for exact claiming and cleanup rules.

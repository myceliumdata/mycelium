# Task: Final cleanup, verification, and TODO/architecture alignment after query-only + core data agent migration

## Objective
Perform a final pass across the entire codebase (source, tests, docs, tmp artifacts if appropriate) to remove any remaining references to public ingest/add support that were not caught by the earlier specialized tasks. Run the full test suite, linter, and a smoke test of the query path through CLI + MCP + direct graph. Update high-level TODO and architecture notes if they still promise old behavior. Leave the project in a clean "queries only, proper core data agent" state.

## Constraints
- The migration is deliberately removing public add support temporarily; do not re-introduce any of it.
- The core_data_agent must be the active specialist for core lookups.
- All public paths (CLI query, MCP query_person) and the internal graph must work for queries.
- Do not delete the old enrich/validator/person_prep files if they are still present — just ensure they are not imported or wired (they are reserved for the "add back later" work).

## Exact Steps
1. Global search (grep) for remaining "ingest", "provided_data", "submit_person_data", "enrich_agent", "validator_agent", "response_ingest_*" etc. in all .py, .md, and other text files. Clean the stragglers.
2. In particular check:
   - Any leftover comments in agents, graphs, models.
   - The full-code-walkthrough.md and architecture.md (even if the dedicated docs task touched them).
   - tmp/ files (update or delete the ones that were teaching ingest usage if they are now misleading).
   - TODO.md — move any public ingest items under a clear "Re-adding data addition later" section.
3. Run:
   - `uv run ruff check src tests`
   - `uv run pytest -q`
   - Quick CLI smoke: `uv run mycelium query --person-key "Nichanan Kesonpat"`
   - If MCP is runnable, a basic import test.
4. If the core_data_agent wiring task was done, do a final verification that a query goes through supervisor → core_data.
5. Produce a short summary of the overall migration state.

## Required Output
- In the done/ output.md: list of final cleanups, full pytest + ruff output, CLI smoke output, and a clear statement "Project is now query-only public interface with core data managed by the CoreDataAgent."
- Any remaining architectural notes for the "internal agent will coordinate adding new data" future work.

Claim this last task from next/ into in-progress/ before starting the final sweep.

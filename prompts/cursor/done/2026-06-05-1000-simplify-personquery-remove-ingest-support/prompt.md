# Task: Simplify PersonQuery model and remove all ingest/add support from it

## Objective
Remove all support for adding/ingesting new persons from the public data model. `PersonQuery` should now ONLY support queries (lookups). The `provided_data` field and all related logic/descriptions must be removed. This is the first step toward a query-only public interface.

We will re-introduce data addition later via an internal coordination agent (see follow-up tasks).

## Constraints & Principles (from docs/architecture.md)
- The public interface will ONLY support queries from now on.
- A proper agent for managing core data will be introduced (in a later task in this series).
- Supervisor remains a thin coordinator/router.
- Core data management (currently via CoreIdentity facade) will be turned into a proper specialist agent node.
- Do not touch storage, CoreIdentity class, enrich/validator/person_prep yet (those will be addressed in subsequent tasks).
- Keep the model minimal: only `person_key` and `requested_attributes` for now.
- Update all docstrings to reflect query-only public use.
- Preserve `Person` model as-is (it will be used internally by the future core data agent).
- Follow existing code style, use Field for descriptions where appropriate.
- This change must not break existing query paths.

## Context
- See `docs/architecture.md` sections on "Core Ingestion Handshake (Phase 1)" (this is being removed from public), supervisor as coordinator, and the note that CoreIdentity is Phase 1.
- The unified `PersonQuery` with `provided_data` was a deliberate Phase 1 simplification for the "Core Ingestion Handshake". We are now reversing the public part of that.
- Current `PersonQuery` in `src/models/state.py` still has `provided_data: Person | None`.
- `MyceliumGraphState` references it indirectly.
- Many docstrings in the file and elsewhere still talk about ingestion.

## Exact Steps
1. Edit ONLY `src/models/state.py`:
   - Remove `provided_data` field from `PersonQuery`.
   - Remove any imports or references to Person inside PersonQuery if only used for that.
   - Simplify the class docstring and field descriptions to be query-only. Remove all mentions of "ingest", "provided_data", "adding", "submit_person_data", "Core Ingestion Handshake".
   - Update `non_core_attributes` if affected (probably not).
   - Add a note in the docstring: "This model is now query-only for the public interface. Data addition support will be re-introduced later via internal agent coordination."
   - Clean up `CORE_PERSON_FIELDS` and `MINIMUM_VIABLE_FIELDS` comments if they mention ingest (they shouldn't need change).
   - Do not change the `Person` class itself yet.
2. Ensure the model still validates for pure query cases (person_key + optional requested_attributes).
3. Run `uv run python -c "from models.state import PersonQuery; print(PersonQuery.model_json_schema())"` (or equivalent) to verify the schema no longer references provided_data.
4. Do **not** update any other files in this task (CLI, MCP, tests, docs, agents, graph, etc. — those are separate tasks).

## Required Output
When complete, create (or follow the workflow to produce):
- Move this prompt to `prompts/cursor/done/2026-06-05-1000-simplify-personquery-remove-ingest-support/prompt.md`
- Produce `prompts/cursor/done/2026-06-05-1000-simplify-personquery-remove-ingest-support/output.md` containing:
  - Summary of changes
  - The diff of src/models/state.py
  - Confirmation that schema is clean
  - Any open questions or notes for follow-up tasks (e.g. "Now remove from MCP in next task")
- Update `prompts/cursor/in-progress/` by removing only this claimed file (per WORKFLOW.md rules).

## How to claim and work (mandatory)
- Before doing any real work, scan `prompts/cursor/next/`, sort by filename, claim the oldest by moving **this specific file** to `prompts/cursor/in-progress/`.
- Do not touch other files in in-progress/.
- After finishing, remove only this file from in-progress/.

Reference: See `prompts/cursor/WORKFLOW.md` and `.cursor/rules/04-cursor-workflow.mdc` for the full protocol.

## Verification
After your changes, a pure query should still construct and validate:
PersonQuery(person_key="Nichanan Kesonpat")
The JSON schema for PersonQuery should have no "provided_data" and no mention of ingestion in top-level description.

Do not run full tests or update callers in this task — leave that for subsequent Cursor tasks in the series.

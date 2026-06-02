# Task: Remove all support for adding/ingesting persons from the CLI

## Objective
Completely remove the `ingest` subcommand and all related code from `src/main.py`. The CLI should now only support `query`. Update help text, argument parsing, and the main dispatch logic accordingly. This enforces the new "public interface only supports queries" rule.

## Constraints & Principles
- Public interface (CLI + MCP) must ONLY support queries from this point forward.
- Do not remove the underlying storage or core data management code (that will be refactored into a proper agent in a later task).
- Preserve all query functionality exactly.
- Update any comments or help strings that mention ingestion.
- The `Person` model and `PersonQuery` (now simplified by prior task) may still be imported; use only for query construction.
- Follow the same style as the existing query parser.

## Context
- See `src/main.py` for the current `ingest_cmd` parser, `_load_person_data`, the `if args.command == "ingest":` block, and related help.
- The ingest path currently builds a `PersonQuery` with `provided_data` (which will have been removed in the prior model-simplification task).
- After this task, running `uv run mycelium ingest ...` should no longer be possible (the subparser should be gone).
- Later tasks will remove `submit_person_data` from MCP and clean up agent/graph paths.

## Exact Steps
1. Edit `src/main.py`:
   - Remove the entire `ingest_cmd = sub.add_parser(...)` block and its arguments.
   - Remove the `ingest_cmd.add_argument` calls.
   - Remove the `_load_person_data` function entirely.
   - In the `if args.command == "ingest":` block (or equivalent dispatch), remove the ingest handling. Keep only the query path.
   - Update the top-level parser description or epilog if it mentions both query and ingest.
   - Update the docstring or comments at the top of `main` if they reference adding data.
   - Clean any remaining references to "ingest" in help texts or error messages.
2. After edit, verify that `uv run mycelium --help` shows only the `query` subcommand.
3. Verify that `uv run mycelium query --person-key "Nichanan Kesonpat"` still works (basic smoke).
4. Do **not** touch MCP, tests, docs, agents, graph, or models in this task.

## Required Output
- Move this prompt to `prompts/cursor/done/2026-06-05-1010-remove-ingest-from-cli/prompt.md`
- Produce `prompts/cursor/done/2026-06-05-1010-remove-ingest-from-cli/output.md` with:
  - Summary of removals
  - Diff of src/main.py
  - Output of `uv run mycelium --help` showing query-only
  - Confirmation that query still works
  - Notes for downstream tasks (e.g. "MCP cleanup next")
- Remove only this file from `prompts/cursor/in-progress/`

## Claiming process (mandatory)
Scan `prompts/cursor/next/`, claim the oldest by moving it to `in-progress/`, execute, then clean only your file from in-progress upon completion. See `prompts/cursor/WORKFLOW.md`.

Do not perform work on any other task files.

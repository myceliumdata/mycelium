# Task: Remove submit_person_data (ingest) tool from the MCP server

## Objective
Remove the `submit_person_data` tool entirely from `src/mycelium_mcp/server.py`. The public MCP interface must only expose query functionality. Update the server description, tool list, and any helper functions or docstrings.

## Constraints & Principles
- Public MCP surface = queries only.
- Keep the internal graph and storage intact (proper core data agent comes later).
- Remove all references to "add a missing person", "provided_data", "ingest", "submit_person_data" from public-facing strings and code paths in this file.
- The `list_person_schema` etc. may stay if they are general, but clean any ingest-specific content.
- Preserve `query_person` exactly.

## Context
- See `src/mycelium_mcp/server.py` for `submit_person_data`, the mcp description that mentions it, the request example with provided_data, the if check for provided_data, and error messages.
- This tool was the MCP counterpart to the CLI ingest command (being removed in parallel task).
- After removal, calling submit_person_data via MCP should not be possible (tool gone).
- Schema listing functions may need minor doc updates.

## Exact Steps
1. Edit `src/mycelium_mcp/server.py`:
   - Remove the entire `def submit_person_data(...)` function.
   - Remove the `@mcp.tool()` decorator and registration for it.
   - Update the top-level `mcp = FastMCP(...)` description to remove any mention of adding persons or submit_person_data.
   - Remove or comment the ingest-specific parts of the `query_person` docstring if they reference adding (keep pure query guidance).
   - Remove the `if query.provided_data is None:` block and related error (this was only for submit).
   - Clean the example JSON in docstrings.
   - If there's a `list_tools` or similar, ensure it no longer lists the removed tool.
   - Update any comments about "MCP `submit_person_data`".
2. Verify the module still imports and the MCP server can be instantiated (`uv run python -c "from mycelium_mcp.server import mcp; print('ok')"`).
3. Do not touch CLI, tests, docs, models, agents, or graph.

## Required Output
- Move prompt to `prompts/cursor/done/2026-06-05-1020-remove-ingest-from-mcp/prompt.md`
- `prompts/cursor/done/2026-06-05-1020-remove-ingest-from-mcp/output.md` with summary, diff, verification output, notes for next tasks.
- Remove only this claimed file from in-progress/.

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly: discover, move to in-progress first, execute only your task, clean only your file on completion.

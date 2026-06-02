# Review — 2026-06-03-0950-update-mcp-server-for-new-response-fields

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Solid MCP integration update. The server now supports optional `thread_id` at the top level of request JSON (stripped before PersonQuery validation), forwards it to `run_query`, and returns full `PersonResponse` (with `trace_id`/`thread_id`) via centralized serialization. Docstrings, instructions, and a new schema resource were updated for discoverability. Behavior for error cases on ingest preserved.

## Strengths

- **Clean extraction of shared logic**:
  - `_parse_query_payload()` handles the optional `thread_id` pop + UUID fallback + validation (mirrors CLI resolver).
  - `_serialize_response()` ensures consistent `model_dump_json(indent=2)` including the correlation fields.
  - `_run_mcp_query()` provides a single happy path for queries.

- **Correct dual use for submit_person_data**:
  - Re-uses the parse logic (so thread_id works for ingest too).
  - Still does its own early bootstrap + error JSON for the provided_data missing case (unchanged per spec).

- **Improved self-documentation**:
  - FastMCP instructions now mention `trace_id`, `thread_id`, and how to pass `thread_id` in requests.
  - Tool docstrings have request/response examples including the new fields.
  - New resource `mycelium://schema/person-response` exposes the full Pydantic schema (useful for AI agents introspecting).

- **Verification**:
  - Ruff clean on the file.
  - pytest (at time) 11 passed.
  - Manual verification via direct module load confirmed: supplied `thread_id` echoed, UUID generated when omitted, ingest path works, error path still plain error JSON.
  - Output.md clearly documents the request/response contract and notes the import gotcha for testing.

- **Scope**: Exactly as requested — only `src/mcp/server.py` + artifacts. No CLI/MCP protocol changes.

## Minor Observations / Non-blocking

- Minor code duplication: `submit_person_data` still calls `_bootstrap()` explicitly + does its own `run_query` call on success, rather than delegating to `_run_mcp_query` (which would have been slightly DRYer but would have required moving the provided_data check inside or after). Acceptable; keeps the special error path isolated.

- The `thread_id` pop happens on the parsed dict before `PersonQuery.model_validate`. If a client sends extra unknown fields, validation will fail (Pydantic default behavior). This is probably desirable (fail fast on bad input) and consistent with before.

- **Pre-existing packaging / import issue flagged**: The project's MCP server lives in `src/mcp/server.py` (top-level `mcp` package). This collides with the official `mcp` SDK (dependency of `fastmcp`). As a result:
  - `uv run mycelium-mcp` (the console script) fails with `ImportError: cannot import name 'run_server' from 'mcp.server'` (gets the SDK's mcp instead).
  - Direct `import mcp.server` in a normal Python env gets the wrong module.
  - Testing requires PYTHONPATH hacks or `importlib.util` loading (as done in review).
  - This name collision predates the 09xx series and was not introduced by this task, but it means the MCP server (now updated for the new fields) is difficult or impossible to run via the documented entry point in a normal installed environment. This is a **deployment / usability show-stopper for anyone wanting to use the MCP interface** (e.g., external agents). Recommend renaming the package (e.g., to `mycelium_mcp` or moving under `mycelium/mcp`) in a follow-up.

- No tests for the MCP layer itself in this increment (out of scope; 0960 focused on core graph + trace capture tests).

## Verdict

**Approved (with noted pre-existing blocker for actual MCP server execution).**

The code changes for supporting the new fields are correct, well-factored, and match the request/response contract described in prior tasks. The helper functions and new schema resource are nice additions for agent usability.

The only real concern is the long-standing package name collision that prevents the `mycelium-mcp` script from working. Since this task completed the MCP side of the 09xx observability work, users following the docs will hit the launch failure immediately.

**Status:** Approved with the packaging caveat noted above. No code changes requested for this diff. The MCP *logic* is ready; the packaging needs a separate fix before the server is practically usable.

Next task (0960) can proceed.
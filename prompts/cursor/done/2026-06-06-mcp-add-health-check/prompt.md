# Task: Add a lightweight health_check tool to the MCP server

## Objective
Add a new `health_check` (or `health`) tool to the Mycelium MCP server. The tool must allow external agents (Claude Desktop etc.) to quickly verify that the server process is responsive, that core subsystems (storage bootstrap, graph singleton) are functional, and that the recent resilience mechanisms (sync checkpointer for MCP, automatic recovery wrapper on query errors) are active. This helps diagnose or prevent "server seems to be stuck" situations after queries (including non-core attribute requests) without requiring a full person lookup.

The health tool must always return a well-formed JSON string (never raise in a way that kills the tool connection).

## Constraints & Principles
- **Strictly limited scope**: Only edit `src/mycelium_mcp/server.py`. Do not touch models, agents, graphs, storage, CLI, tests source, docs, or architecture files except for running verification commands.
- Reference and align with the query-only public surface from `docs/architecture.md`.
- Preserve all existing behavior for `query_person`, `list_specialist_routing`, the resources, _bootstrap, _run_mcp_query (including the recovery try/except that was added to prevent permanent stuck state), and the MYCELIUM_USE_SYNC_CHECKPOINTER forcing.
- Do not introduce new Pydantic models (return plain JSON string, similar to list_specialist_routing).
- Small, reviewable change only.
- Follow "Prefer simplification" — keep the implementation minimal.
- Update the FastMCP `instructions=` string to mention the new tool so Claude knows to use it for diagnostics.
- After implementation, only run smoke tests (`uv run pytest -m smoke -q`) by default. If a new test is added it must be classified by Grok (this prompt expects smoke-level verification only; a simple import + call smoke in an existing or new marked test would be full only if it touches real DB/graph — avoid adding tests unless necessary for the task).
- Do not change the recent sync checkpointer or recovery logic (we are not undoing prior work).

## Context
- Current MCP tools (see `src/mycelium_mcp/server.py`): `query_person(query_json: str)`, `list_specialist_routing()`. Resources for schemas.
- The server is long-running (FastMCP stdio). Multiple sequential calls from Claude can surface loop/checkpointer issues (documented in recent 1120 review and 2026-06-05-1120 prompt).
- Recent stabilization (kept as-is): env forced to sync saver + recovery in _run_mcp_query that calls reset_core_graph on error and returns graceful PersonResponse-shaped error JSON.
- A health tool gives Claude (and future external agents) a safe, cheap way to self-check "is Mycelium MCP healthy right now?" and to surface useful info like active checkpointer type and that recovery is available.
- Aligns with TODO observability items and the general need for better MCP surface diagnostics (without re-adding full status enums yet).
- References: `prompts/resets/2026-06-05_mvp_current.md`, `docs/architecture.md` (MCP section), `prompts/cursor/WORKFLOW.md`, `TODO.md` (observability + re-evaluate status categories), the 1120 cleanup prompt and its review.

See the server implementation for _bootstrap, how list_specialist_routing works (lightweight, no full query), and the structure of returned JSON strings.

## Exact Steps (perform in order)
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, find this prompt (named e.g. 2026-06-06-mcp-health-tool.md or similar timestamped), **immediately move** it to `prompts/cursor/in-progress/<same-name>/`. Only then begin work. Document the move in your output. Never work on a file still in next/.

2. **Discovery**: Read `src/mycelium_mcp/server.py` fully. Also read relevant sections of `docs/architecture.md` (public interface + MCP) and `prompts/resets/2026-06-05_mvp_current.md` (current task and notes on MCP/CLI). Run a command to list current registered tools if helpful (`uv run python -c "..."` using the server). Note the exact location where new @mcp.tool should be added (after list_specialist_routing is fine).

3. **Implement the health tool (only in src/mycelium_mcp/server.py)**:
   - Add a new function (can be internal _health_check or directly the tool).
   - Decorate with @mcp.tool.
   - Name the tool `health_check` (or `health` — choose clear one; document choice).
   - Signature: `def health_check() -> str:`
   - Inside:
     - Call _bootstrap() (like the other tools do).
     - Perform a small set of checks (all wrapped in try/except so the tool itself never fails hard):
       - Storage can be obtained via get_storage.
       - Graph singleton obtainable via get_core_graph (from graphs.core).
       - Existing lightweight tool works: call list_specialist_routing and verify basic content.
       - Optionally (and safely): perform one internal "ping" query_person using a hardcoded known-good person_key from the seed (e.g. "Nichanan Kesonpat" or "person-0001"). Capture whether it returned results without hitting the internal error path. This exercises the full stabilized query path (sync checkpointer + recovery) without user input.
     - Detect/report that the sync checkpointer + recovery mechanisms are active (hardcode or inspect the env + presence of recovery code path; keep simple).
     - Assemble and return a JSON string (pretty printed) with at minimum:
       {
         "status": "ok" | "degraded",
         "checks": { "storage": "ok", "graph": "ok", "lightweight_tool": "ok", "ping_query": "ok" | "degraded", ... },
         "info": {
           "checkpointer": "sync (forced for MCP)",
           "recovery_wrapper": "active",
           "server": "mycelium-mcp"
         },
         "message": "Mycelium MCP server is responsive."
       }
   - Make the tool always succeed in returning parseable JSON (use the same pattern as the error fallback in _run_mcp_query).
   - Update the top-level `mcp = FastMCP( instructions=( ... ) )` string to mention the new tool, e.g. add "Use health_check() to verify the server is responsive and to inspect internal stabilization (sync checkpointer, automatic recovery after query issues)."

4. **Verification (smoke only by default)**:
   - Run `uv run pytest -m smoke -q` and include output.
   - Manually smoke the new tool: `uv run python -c '
     import json, os
     os.environ["MYCELIUM_USE_SYNC_CHECKPOINTER"]="1"
     from mycelium_mcp.server import health_check
     h = health_check()
     print(h)
     data = json.loads(h)
     assert "status" in data
     print("health_check smoke: ok")
     ' `
   - Confirm existing tools still work (`query_person` on a seed person, `list_specialist_routing`).
   - Confirm the module can still be imported and mcp.run() path is intact (no syntax/import breakage).

5. **Output artifacts** (exactly as required by WORKFLOW):
   - Move the original prompt file into `prompts/cursor/done/<timestamp>-mcp-add-health-check/prompt.md`
   - Create `prompts/cursor/done/<same>/output.md` containing:
     - Clear summary of what was changed and decisions (why this shape for health JSON, choice of checks, why no new models).
     - The diff (or description of edit).
     - Full output of the smoke commands you ran.
     - Any open questions or follow-ups (e.g. "should we also add a resource later? should health be called automatically by Claude on first connect?").
   - Remove **only** the file you claimed from `prompts/cursor/in-progress/`.
   - Optionally create a `review.md` placeholder, but not required.

6. **Process hygiene**:
   - Follow claiming, in-progress, done exactly (see WORKFLOW.md and .cursor/rules/04-cursor-workflow.mdc).
   - If at any point you feel you must edit outside src/mycelium_mcp/server.py to "make it work", **stop immediately**, document in output.md + review-notes.md, and create a follow-up prompt in next/ instead of making the out-of-scope change.
   - Run only smoke tests unless you add a new test (in which case ask Grok via the output for category and run the appropriate one immediately).
   - Consider whether this belongs in TODO.md (lightweight addition under observability or MCP surface); if yes, make a minimal update only if it fits the "only edit server.py" rule — otherwise note it for a separate prompt.

## Scope Boundaries (Strict)
You may only modify files under the following paths:
- `src/mycelium_mcp/server.py`

**Out of Scope (Do Not Touch)**
- Any file under `src/models/`, `src/agents/`, `src/graphs/`, `src/storage/`, `src/main.py`, `tests/`, `docs/`, `README.md`, `prompts/resets/`, `TODO.md` (except noting in your output.md that a follow-up may be needed), `bin/`, or anything else.
- Do not introduce new files except the required output artifacts under the done/ directory for *this* task.
- Do not change the behavior or signature of existing tools/resources.
- Do not undo or modify the sync checkpointer forcing or the recovery logic in _run_mcp_query.

If you determine that changes outside this scope are necessary to keep the system working:
- **Stop immediately.**
- Clearly document the problem in your `output.md` and `review-notes.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory. Violating scope boundaries will be treated as a failure to follow instructions.

## Test Execution Policy
- Default: `uv run pytest -m smoke -q` only.
- The health_check implementation should be verifiable with a simple import + direct call smoke (no real new full integration test required for this task).
- If you feel a test addition is needed, stop and document; Grok will assign the marker.

## Required Output Location & Artifacts
- Follow the directory move + creation rules in WORKFLOW.md exactly.
- Primary: `prompts/cursor/done/<your-timestamp-slug>/output.md`
- The claimed prompt moved to the done/ subdir as `prompt.md`

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly before doing any implementation work.

## Suggested Acceptance
After Cursor delivers, we (Grok + Paul) will review the output.md, manually invoke the health_check via Claude Desktop or python, confirm it reports "ok" with the expected checks (including recovery info), confirm no regression on normal queries, and either add review.md or create follow-up prompt.

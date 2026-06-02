# Task: Update CLI to Support thread_id and Include New IDs in Output

**Created:** 2026-06-03

**Objective:** Update the CLI so that it properly accepts `--thread-id`, passes it through to `run_query`, and displays the new `trace_id` and `thread_id` fields in the response output.

**References:**
- Previous tasks in the 09xx series
- `src/main.py`

---

## Scope (Strict)

**In scope:**
- Update argument parsing for the `query` and `ingest` commands to support `--thread-id`.
- Pass the `thread_id` through to `run_query`.
- Ensure the printed JSON response now includes the new `trace_id` and `thread_id` fields.
- Minor output formatting if needed to keep the response readable.

**Out of scope:**
- Changes to MCP server.
- Major changes to response formatting or new output modes.
- Adding a `--trace-url` flag (can be a follow-up).

---

## Step-by-Step Instructions

1. **Claim the task**

2. **Update argument parsing**
   - Add `--thread-id` support to both `query` and `ingest` subcommands (it may already exist partially — make sure it is correctly wired).

3. **Pass thread_id into run_query**
   - Ensure the value from the CLI (or a generated default) is passed to `run_query(..., thread_id=...)`.

4. **Verify response output**
   - Confirm that when the new fields are populated, they appear in the JSON printed to the console.

5. **Test manually**
   - Run a few CLI queries and ingest commands to confirm `thread_id` is accepted and the new fields appear in output.

6. **Verify**
   - `uv run ruff check src`
   - Basic manual testing of the CLI.

---

## Success Criteria

- [ ] CLI accepts `--thread-id` for both query and ingest.
- [ ] The supplied (or generated) `thread_id` is passed to the graph.
- [ ] The final JSON output includes `trace_id` and `thread_id` when present.
- [ ] No breakage to existing CLI behavior.

---

**Keep this task small and focused on CLI integration.** Documentation and MCP updates come later.
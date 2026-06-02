# Task: Update MCP Server for New trace_id and thread_id Fields

**Created:** 2026-06-03

**Objective:** Update the MCP server so that it properly passes `thread_id` through to queries/ingests and returns the new `trace_id` and `thread_id` fields in responses.

**References:**
- Previous tasks in the 09xx series
- `src/mcp/server.py`

---

## Scope (Strict)

**In scope:**
- Ensure `query_person` and `submit_person_data` correctly accept and forward `thread_id`.
- Verify that the returned `PersonResponse` now includes `trace_id` and `thread_id`.
- Update any docstrings or inline documentation in the MCP server to reflect the new fields.

**Out of scope:**
- Major changes to the MCP protocol or adding new tools.
- CLI changes (handled in previous task).
- Tests and broader documentation.

---

## Step-by-Step Instructions

1. **Claim the task**

2. **Review current MCP handlers**
   - Look at how `query_person` and `submit_person_data` are implemented.
   - Check how `thread_id` (if supported) flows today.

3. **Ensure thread_id is passed through**
   - Make sure any `thread_id` provided by the MCP caller is forwarded to `run_query`.

4. **Confirm new fields are returned**
   - Since the response model now includes the fields, verify they will be serialized correctly in the MCP JSON responses.

5. **Update documentation**
   - Lightly update docstrings or comments in `server.py` to mention the new fields.

6. **Verify**
   - Ruff check
   - If possible, manually test the MCP server (or at least confirm it starts cleanly).

---

## Success Criteria

- [ ] `thread_id` from MCP clients is passed to the graph.
- [ ] Responses from the MCP server include the new `trace_id` and `thread_id` fields.
- [ ] No breakage to existing MCP behavior.
- [ ] Code is clean.

---

**Keep this task narrowly focused on MCP integration.** Broader documentation updates come later.

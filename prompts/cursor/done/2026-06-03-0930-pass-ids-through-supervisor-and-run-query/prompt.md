# Task: Pass thread_id and trace_id Through the Supervisor and run_query

**Created:** 2026-06-03

**Objective:** Ensure that the caller's `thread_id` and the captured LangSmith `trace_id` are passed all the way through the supervisor into the response construction logic.

**References:**
- Previous tasks in the 09xx series (model update, trace capture, response builders)
- `src/graphs/core.py` (`run_query`)
- `src/agents/supervisor.py`

---

## Scope (Strict)

**In scope:**
- Modify `run_query` to accept the captured `trace_id` (from the previous capture task) and pass both `thread_id` and `trace_id` down to the graph / supervisor.
- Update `supervisor_agent` and related functions to carry these IDs through to the final `PersonResponse`.
- Ensure that when a caller supplies a `thread_id`, it is echoed back in the response.

**Out of scope:**
- Changes to CLI or MCP argument parsing (those come later).
- Response builder updates (assumed done in previous task).
- Tests and documentation.

---

## Step-by-Step Instructions

1. **Claim the task**

2. **Update `run_query`**
   - Modify the function signature (or internal logic) to accept the `trace_id` captured from LangSmith.
   - Pass both `thread_id` and `trace_id` into the initial state or directly to the supervisor when constructing the response.

3. **Update the supervisor**
   - Modify `supervisor_agent` (and `_apply_decision` if used) to accept and forward `thread_id` and `trace_id` when creating the final response.
   - Make sure that for normal lookup paths, the supplied `thread_id` is included in the response.

4. **Ensure consistency**
   - For the ingestion path, make sure the IDs are also carried through to success and failure responses.

5. **Verify**
   - Run ruff and a subset of tests to ensure nothing is broken.
   - Manually inspect that the IDs can flow through to a `PersonResponse`.

---

## Success Criteria

- [ ] `run_query` can receive and forward `thread_id` + `trace_id`.
- [ ] The supervisor correctly includes the IDs in responses for both lookup and ingest paths.
- [ ] No breakage to existing behavior when IDs are not yet fully wired from callers.
- [ ] Code is clean and reviewable.

---

**This task is the "plumbing" step** that connects the capture point to the response builders. Keep changes focused and small.
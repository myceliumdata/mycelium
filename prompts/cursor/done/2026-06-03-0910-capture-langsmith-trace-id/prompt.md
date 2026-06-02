# Task: Capture LangSmith trace_id During Graph Execution

**Created:** 2026-06-03

**Objective:** Modify the query execution path so that the LangSmith `trace_id` for the current invocation is captured and made available to be included in the `PersonResponse`.

**References:**
- Task `2026-06-03-0900-add-trace-id-and-thread-id-to-person-response` (adds the fields)
- `src/graphs/core.py` (run_query function)
- LangSmith integration for tracing

---

## Background

When LangSmith tracing is enabled, every `graph.invoke()` creates a trace with a unique `trace_id`. We need to capture this ID so it can be returned in the response for observability and debugging.

---

## Scope (Strict)

**In scope:**
- Update `run_query` (and/or the graph invocation) to capture the current LangSmith trace ID.
- Make the captured `trace_id` available to downstream code that builds the `PersonResponse`.
- Use LangSmith's recommended way to retrieve the current trace ID (e.g. `get_current_run_tree()` or equivalent).

**Out of scope:**
- Adding the ID to the actual `PersonResponse` (this will be done after the model is updated).
- Changes to CLI, MCP, or response builders.
- Any changes to how `thread_id` is handled.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file to `prompts/cursor/in-progress/`.

2. **Research the best way to capture the trace ID**
   - Investigate how to reliably get the current LangSmith trace ID after (or during) a `graph.invoke()` call when tracing is enabled.
   - Common approaches include using `langsmith.get_current_run_tree()` inside the execution or using a callback handler.

3. **Implement capture logic**
   - Modify `src/graphs/core.py` (the `run_query` function) to capture the `trace_id`.
   - Store it temporarily so it can be passed to response construction logic later.
   - Handle the case where tracing is disabled gracefully (return `None` or empty string).

4. **Verify**
   - Manually test that a `trace_id` is captured when LangSmith tracing is enabled.
   - Ensure the code does not break when tracing is disabled.
   - Run `uv run pytest` and `uv run ruff check`.

5. **Document the approach**
   - In your `output.md`, clearly explain how the trace ID is being captured and any assumptions or requirements (e.g. environment variables that must be set).

---

## Success Criteria

- [ ] The LangSmith `trace_id` for the current graph invocation is reliably captured in `run_query`.
- [ ] The code gracefully handles cases where tracing is not enabled.
- [ ] No behavior change to existing query responses.
- [ ] Tests pass and ruff is clean.

---

**Keep this task focused purely on capturing the trace ID.** Do not start wiring it into responses yet — that will be a follow-up task.
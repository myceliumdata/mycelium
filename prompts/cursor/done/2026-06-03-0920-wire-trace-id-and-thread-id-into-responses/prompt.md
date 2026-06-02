# Task: Wire trace_id and thread_id Into Response Construction

**Created:** 2026-06-03

**Objective:** Update the response construction logic so that `trace_id` and `thread_id` are passed through and included in the final `PersonResponse`.

**References:**
- Task `2026-06-03-0900` (added fields to the model)
- Task `2026-06-03-0910` (captures the LangSmith trace_id)
- `src/agents/responses.py`
- `src/agents/routing.py`

---

## Scope (Strict)

**In scope:**
- Update the response builder functions in `responses.py` to accept `trace_id` and `thread_id` and include them in the returned `PersonResponse`.
- Update `routing.py` (specifically `evaluate_supervisor_turn` and `SupervisorDecision`) to carry these IDs through the decision process.
- Update the call sites in `supervisor.py` that create or return `SupervisorDecision` objects to pass the IDs when available.

**Out of scope:**
- Changes to the CLI or MCP server.
- Updating tests.
- Documentation updates.
- Any changes to how the IDs are captured.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file to `prompts/cursor/in-progress/`.

2. **Update the response builders**
   - Modify the functions in `src/agents/responses.py` (`response_found`, `response_not_found`, `response_non_core`, `response_ingest_success`, `response_ingest_failure`, etc.) to accept optional `trace_id` and `thread_id` parameters.
   - Include the values in the constructed `PersonResponse`.

3. **Update the routing layer**
   - Extend `SupervisorDecision` (or create a way to carry the IDs) so that `trace_id` and `thread_id` can flow through `evaluate_supervisor_turn`.
   - Update all call sites inside `evaluate_supervisor_turn` to pass the IDs to the response builder functions.

4. **Update the supervisor**
   - Modify `supervisor_agent` and `_apply_decision` (if needed) to ensure the IDs from the decision are properly included in the final response returned to the graph.

5. **Verify compilation and basic behavior**
   - Run `uv run ruff check src`
   - Run `uv run pytest` (some tests may need temporary adjustment later, but the code should at least not break at import time).

6. **Document the changes**
   - In your `output.md`, clearly describe how the IDs now flow from capture → routing → response builders.

---

## Success Criteria

- [ ] All response builder functions can accept and include `trace_id` and `thread_id`.
- [ ] `evaluate_supervisor_turn` can carry the IDs through the decision process.
- [ ] The supervisor correctly propagates the IDs into the final `PersonResponse`.
- [ ] No behavior change for existing fields or logic when the IDs are not yet populated.
- [ ] Ruff is clean.

---

**This task is purely about plumbing the IDs through the existing response construction machinery.** Do not start updating CLI, MCP, or tests yet.
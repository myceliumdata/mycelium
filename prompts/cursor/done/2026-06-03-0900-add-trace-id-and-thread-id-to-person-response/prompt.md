# Task: Add trace_id and thread_id to PersonResponse

**Created:** 2026-06-03

**Objective:** Extend the `PersonResponse` model to include `trace_id` and `thread_id` as first-class top-level fields.

**Context:**  
We have decided to surface both the LangSmith `trace_id` and the conversation `thread_id` directly in responses (not buried in `debug`). This enables external agents to correlate calls and allows operators to investigate issues in production via LangSmith.

**References:**
- Recent design discussion on observability and external agent correlation
- `src/models/state.py` (current `PersonResponse`)
- `docs/architecture.md`

---

## Scope (Strict)

**In scope:**
- Add two new optional (or required) fields to `PersonResponse`:
  - `trace_id: str | None`
  - `thread_id: str | None`
- Update the model definition and any related Pydantic configuration.
- Update any existing construction of `PersonResponse` in `responses.py` to accept and pass through these IDs (they can be `None` for now).

**Out of scope:**
- Actually populating the fields with real values (this will be done in follow-up tasks).
- Changing how responses are built in `routing.py` or `supervisor.py`.
- Updating CLI, MCP, tests, or documentation.
- Any changes to `debug` field behavior.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file to `prompts/cursor/in-progress/`.

2. **Update the model**
   - In `src/models/state.py`, add the two new fields to `PersonResponse`.
   - Decide on types (recommended: `str | None = None` for both, or make them required `str` if we decide they will always be present going forward).
   - Add clear docstrings explaining the purpose of each field.

3. **Update response builders (minimal)**
   - In `src/agents/responses.py`, update the response builder functions to accept optional `trace_id` and `thread_id` parameters and include them in the returned `PersonResponse`.

4. **Verify**
   - Run `uv run pytest`
   - Run `uv run ruff check src tests`
   - Manually construct a `PersonResponse` in a Python snippet to confirm the new fields work.

5. **Deliver artifacts**
   - Create the done folder and follow the standard workflow.
   - Clearly document the new fields and their intended semantics in `output.md`.

---

## Success Criteria

- [ ] `PersonResponse` has two new fields: `trace_id` and `thread_id`.
- [ ] The model remains valid and serializes correctly.
- [ ] Response builder functions can accept the new fields.
- [ ] All tests still pass.
- [ ] Ruff is clean.
- [ ] No behavior changes to existing fields or logic.

---

**Keep this change extremely small.** This task is only about extending the data model. Population of the fields and downstream updates will happen in subsequent tasks.
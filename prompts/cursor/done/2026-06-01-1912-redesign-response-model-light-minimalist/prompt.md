# Task: Redesign PersonResponse to a Minimalist Model

**Created:** 2026-06-01  
**Objective:** Replace the current heavy `PersonResponse` (with `status`, `person`, `data`, `data_request`, `deferred_attributes`, etc.) with a very lightweight structure aligned with the current architectural direction.

**References:**
- `docs/architecture.md` (especially the principles around supervisor as coordinator and minimal external contracts)
- Recent design discussion (light approach, unstructured messages for agent reasoning)
- `src/models/state.py`
- `src/agents/supervisor.py`

---

## Current Problems (Context for Cursor)

The existing `PersonResponse` leaks too many internal concepts to external callers (both CLI users and MCP agents):

- Multiple `status` values (`found`, `specialist_required`, `data_request`, etc.)
- Separate `person` + `data` fields (mostly redundant)
- `data_request`, `deferred_attributes`, `errors` objects
- These make the external interface chatty about our internal routing, ingestion workflow, and specialist boundary.

We are moving to a much lighter model.

## Target Design (Agreed)

The new public response should be extremely minimal:

```python
class PersonResponse(BaseModel):
    """Lightweight response for external consumers (CLI + MCP agents)."""

    results: list[dict] = Field(
        default_factory=list,
        description="Core person records as plain dicts (id, name, employer only). Always a list."
    )
    message: str = Field(
        default="",
        description="Human- and agent-readable narrative. This is the primary channel for communicating state, progress, and reasoning to callers. It can evolve over time (e.g. 'Searching for email addresses...', 'We have the core record but are still researching contact details')."
    )
    debug: str = Field(
        default="",
        description="Internal diagnostic information only. Not intended for external consumption. Include the original query details here."
    )
```

**Key principles for this redesign:**
- `results` must contain **plain Python dicts**, not `Person` model instances (we are using Option B — no leaking the `Person` Pydantic model externally).
- `message` is for **external agents and humans** to reason with. It should be rich and natural-language friendly.
- `debug` is strictly for us during development and debugging. Put the original `person_key` + `requested_attributes` here, plus any internal notes.
- No `status` field for now. We are deliberately trying the unstructured + rich message approach.
- The response must remain useful for both simple synchronous lookups and future asynchronous research flows.

**Example use case to support:**
When we have a core record for someone (e.g. "Paul Murphy") but the caller asked for `email`, and we haven't found any emails yet, we should be able to return the person in `results` while using `message` to say something like: "We have a core record for Paul Murphy, but we're still researching email addresses."

---

## Scope Boundaries (Strict)

**You may modify:**
- `src/models/state.py` — Define the new `PersonResponse`. You may also clean up or deprecate `DataRequest` and the old status literals if they are no longer used after the changes.
- `src/agents/supervisor.py` — Update all paths that construct `PersonResponse` to use the new shape. Keep internal `audit_log` and `MyceliumGraphState` working.
- `src/mcp/server.py` — Update response handling to return the new format.
- `src/main.py` — Update the CLI so `query` and other commands print the new shape sensibly.
- Related tests (only as needed to keep the suite green).

**You may read (read-only) for understanding:**
- `src/graphs/core.py`
- Any tests that exercise query/ingest flows
- `docs/architecture.md`

**Out of Scope (Do Not Touch):**
- `PersonQuery` input model (leave as-is for this task)
- `Person` model itself (keep it for internal use)
- Storage layer (`src/storage/core.py`)
- Full ingestion flow rework
- Adding new features or async behavior
- Updating documentation beyond code comments

If you believe changes outside this scope are required, **stop** and document the issue in your output.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Scan `prompts/cursor/next/`
   - Move this file to `prompts/cursor/in-progress/` before doing any real work.

2. **Design the new model**
   - Introduce the new `PersonResponse` as shown above in `src/models/state.py`.
   - Keep `Person` as an internal model (it is still useful in storage and supervisor logic).
   - When populating `results`, convert to plain dicts using something like `person.core_dict()` or direct construction. Do **not** put `Person` instances into the response.

3. **Update the supervisor**
   - Refactor `supervisor_agent` to build responses using only `results`, `message`, and `debug`.
   - Remove all usage of the old `status`, `person`, `data`, `data_request`, `deferred_attributes`, etc. from response construction.
   - For the `debug` field, include the original query information (at minimum `person_key` and `requested_attributes`).
   - Preserve all existing `audit_log` entries for now.

4. **Update call sites**
   - Modify the MCP server to return the new response shape.
   - Update the CLI (`main.py`) so that query results are printed in a readable way under the new structure.
   - Ensure `run_query` still returns a valid `PersonResponse`.

5. **Handle the graph state**
   - `MyceliumGraphState` currently references `response: PersonResponse`. Update as needed so the graph continues to function.

6. **Testing & Verification**
   - Run the existing test suite and fix any breakage caused by the shape change.
   - Manually test a few scenarios via the CLI:
     - Query an existing person with only core fields
     - Query an existing person and request non-core attributes (use the "still researching" message pattern)
     - Query a completely unknown person
   - Confirm that `results` contains only plain dicts.

7. **Deliver artifacts**
   - Create `prompts/cursor/done/2026-06-01-1912-redesign-response-model-light-minimalist/`
   - Include `prompt.md`, a detailed `output.md`, and any relevant diffs or notes.
   - Cleanly remove only this task file from `in-progress/`.

---

## Success Criteria

- [ ] `PersonResponse` has exactly three fields: `results` (list of dicts), `message` (str), `debug` (str)
- [ ] No `status`, `person`, `data`, `data_request`, `deferred_attributes`, or similar fields remain in the public response model
- [ ] `results` always contains plain dictionaries (never `Person` instances)
- [ ] Original query information lives in `debug`, not in the public part of the response
- [ ] The supervisor produces responses using the new model across all paths (found, missing, non-core requests, ingest, etc.)
- [ ] CLI and MCP continue to function and return the new shape
- [ ] Tests pass
- [ ] The "still researching non-core attributes" use case is supportable via the `message` field

---

## Notes for Cursor

- This is a deliberate simplification. Resist the urge to add new structured fields "just in case."
- Focus on making `message` the primary vehicle for communicating state to external agents.
- Keep the change as small and reviewable as possible while achieving the new shape.
- If you find the old `DataRequest` or status literals are now dead code, you may remove them, but this is secondary.

Good luck. This is an important step toward a cleaner external contract.
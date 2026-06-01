# Task: Redesign PersonResponse to a Minimalist Model

**Created:** 2026-06-01  
**Objective:** Replace the current heavy `PersonResponse` model with a very lightweight structure that aligns with our current architectural direction.

**References:**
- `docs/architecture.md`
- Recent design discussions on minimal external contracts and agent-friendly messaging

---

## Current Problems

The existing `PersonResponse` leaks internal implementation details to external callers (CLI and MCP agents):

- Multiple `status` values (`found`, `specialist_required`, `data_request`, etc.)
- Redundant `person` + `data` fields
- `data_request`, `deferred_attributes`, and `errors` structures
- This makes the public interface chatty about our internal routing, specialist boundary, and ingestion workflow.

We are deliberately moving to a much lighter model.

## Target Design

The new public response should be minimal:

```python
class PersonResponse(BaseModel):
    """Lightweight response for external consumers (CLI + MCP agents)."""

    results: list[dict] = Field(
        default_factory=list,
        description="Core person records as plain dictionaries (only id, name, employer)."
    )
    message: str = Field(
        default="",
        description="Human- and agent-readable narrative. Primary channel for communicating state, progress, and reasoning to callers."
    )
    debug: str = Field(
        default="",
        description="Internal diagnostic information only. Not intended for external consumption."
    )
```

**Key rules for this redesign:**
- `results` must contain **plain Python dicts** only. Never `Person` model instances.
- Each dict in `results` should contain at most the three core fields: `id`, `name`, and `employer`.
- `message` is the main vehicle for talking to external agents and humans.
- `debug` is strictly internal.

## Communication Philosophy

- `results` contains only structured, factual core data. It should be reliable and idempotent.
- `message` is the primary way we communicate with external agents and humans. It can (and should) contain natural language reasoning, progress updates, partial knowledge, or negative knowledge (e.g., "We have a core record for Paul Murphy, but we are still researching email addresses.").
- `debug` exists only for our visibility during development and debugging. External callers should never need to read or depend on it.

---

## Scope Boundaries (Strict)

**You may modify:**
- `src/models/state.py` — Define the new `PersonResponse`.
- `src/agents/supervisor.py` — Update response construction to use the new shape.
- `src/mcp/server.py` — Update to return the new response format.
- `src/main.py` — Update CLI output for the new shape.

**You must NOT:**
- Touch or improve the ingestion handshake / flow. If old ingestion-related response paths are hit, stub them with a clear message such as "Ingestion flow is not yet implemented" and do not attempt to make it functional.
- Redesign or significantly change `MyceliumGraphState`. Make only the minimal adjustments required to keep the graph compiling and running.
- Perform broad cleanup of now-unused fields/models (e.g. `DataRequest`, old status literals). Leave them in place for now.

**Out of Scope:**
- Changes to `PersonQuery`
- Changes to the storage layer
- Any work on making specialist routing or asynchronous research actually functional

If you believe work outside this scope is required to complete the task, **stop** and document it clearly.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before beginning implementation work.

2. **Implement the new model**
   - Add the new `PersonResponse` in `src/models/state.py` exactly as defined in the Target Design section.
   - When populating `results`, ensure you are returning plain dicts (e.g. via `person.core_dict()` or equivalent). Do not return `Person` instances.

3. **Update the supervisor**
   - Modify `supervisor_agent` (and any helper logic) to construct responses using only `results`, `message`, and `debug`.
   - Remove usage of the old `status`, `person`, `data`, `data_request`, `deferred_attributes`, etc. from response objects.
   - Place original query information (`person_key` and `requested_attributes`) into the `debug` field.
   - For any paths related to the old ingestion flow, return a response with an appropriate `message` indicating the flow is not yet implemented.

4. **Update call sites**
   - Update `src/mcp/server.py` to return the new response shape.
   - Update `src/main.py` so CLI commands produce readable output under the new structure.

5. **Graph state**
   - Make only the minimal changes to `MyceliumGraphState` necessary to keep the graph functional. Do not refactor or simplify it as part of this task.

6. **Testing & Verification**
   - Fix any tests that break due to the response shape change.
   - Verify the following scenarios work via the CLI:
     - Query an existing person (core fields only)
     - Query an existing person while requesting non-core attributes (demonstrate use of `message` to indicate ongoing research)
     - Query a person that does not exist
   - Confirm that `results` contains only plain dicts with core fields.

7. **Deliver artifacts**
   - Create the done folder: `prompts/cursor/done/2026-06-01-1912-redesign-response-model-light-minimalist/`
   - Include `prompt.md`, `output.md`, and any relevant notes or diffs.
   - Remove only this file from `in-progress/`.

---

## Success Criteria

- [ ] `PersonResponse` has exactly three fields: `results` (`list[dict]`), `message` (`str`), and `debug` (`str`)
- [ ] No `status`, `person`, `data`, `data_request`, or `deferred_attributes` fields are used when constructing public responses
- [ ] `results` contains only plain dictionaries (never `Person` instances) with at most `id`, `name`, and `employer`
- [ ] Original query information is placed in `debug`, not exposed publicly
- [ ] The supervisor produces valid responses in the new format across lookup paths
- [ ] CLI and MCP continue to function with the new shape
- [ ] Ingestion-related paths are stubbed (not improved or reworked)
- [ ] `MyceliumGraphState` is left mostly untouched
- [ ] Tests pass after the change
- [ ] The "still researching non-core attributes" pattern is demonstrable via the `message` field

---

## Follow-up Work (Add These to TODO.md)

- Revisit and properly design the ingestion handshake / `data_request` flow.
- Clean up now-unused code (`DataRequest`, old status literals, related fields in `PersonResponse` and `MyceliumGraphState`).
- Re-evaluate whether a lightweight machine-readable `status` field is needed after real usage.

---

**Do not expand scope.** This task is intentionally narrow. Focus on delivering the new minimal response shape cleanly.
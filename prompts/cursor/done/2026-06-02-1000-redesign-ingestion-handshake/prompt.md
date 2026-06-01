# Task: Redesign the Ingestion Handshake (data_request flow)

**Created:** 2026-06-02

**Objective:** Design and implement a clean, minimal ingestion flow for bringing new people into the core dataset. Replace the current stub ("Ingestion flow is not yet implemented") with a proper, well-scoped mechanism that aligns with the minimalist `PersonResponse` model and the overall architecture.

**References:**
- `docs/architecture.md`
- Current stub implementation in `src/agents/supervisor.py`
- The lightweight `PersonResponse` (`results`, `message`, `debug`) from task 1912
- TODO item: "Revisit and properly design the ingestion handshake / `data_request` flow"

---

## Background

After the minimalist `PersonResponse` redesign (1912), all ingestion-related paths were intentionally stubbed. When a caller tries to ingest via `provided_data` or queries a missing person, the system now returns:

```json
{
  "results": [],
  "message": "Ingestion flow is not yet implemented.",
  "debug": "..."
}
```

We need a proper, lightweight design for how external agents (and humans via CLI) can add new core records.

## Goals for the New Design

- Keep the external interface minimal and aligned with `results` / `message` / `debug`.
- Make the flow simple and explicit.
- Avoid turning the query API into a complex state machine.
- Support the principle that the supervisor should act primarily as a coordinator/router.
- The flow should feel natural for AI agents to use.

## Out of Scope (Strict)

- Do **not** implement full enrichment or specialist routing as part of this task.
- Do **not** add validation logic beyond basic core field presence (that can be a follow-up).
- Do **not** redesign `MyceliumGraphState` or the internal graph nodes unless absolutely necessary.
- Avoid reintroducing heavy structures like the old `DataRequest` model unless there is a very clear justification.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file to `prompts/cursor/in-progress/`.

2. **Analyze the current state**
   - Review how `provided_data` is currently handled in `supervisor.py` and `graphs/core.py`.
   - Review how the CLI `ingest` command works in `src/main.py`.
   - Review the MCP `submit_person_data` implementation.
   - Document the exact current behavior in your `output.md`.

3. **Propose a design**
   In your thinking and `output.md`, present a clear proposed design for the ingestion flow. At minimum, address:
   - How should an external caller request to add a new person?
   - What should the response look like when a person is missing (using the current `results`/`message`/`debug` model)?
   - Should there be a dedicated "ingest" path, or should it be triggered through the normal query mechanism?
   - How do we communicate success vs. failure in the new lightweight format?
   - Should the caller supply the full minimum viable record upfront, or should there be a two-step process?

4. **Implement the chosen design**
   - Update `src/agents/supervisor.py` to handle ingestion according to the agreed design.
   - Update `src/main.py` (CLI) if the `ingest` command needs adjustment.
   - Update `src/mcp/server.py` if the `submit_person_data` behavior needs to change.
   - Keep changes minimal and reviewable.

5. **Update tests**
   - Adjust existing tests as needed.
   - Add at least one or two clear tests that exercise the new ingestion flow.

6. **Update documentation**
   - Add a brief note in `TODO.md` marking this item complete.
   - If useful, add a short explanation in `docs/architecture.md` or a code comment.

7. **Deliver artifacts**
   - Follow the standard workflow: create the done folder with `prompt.md`, `output.md`, etc.
   - Remove only this file from `in-progress/`.

---

## Success Criteria

- [ ] There is a clear, working way for external callers to add new core people.
- [ ] The flow uses the minimalist `PersonResponse` shape (`results` / `message` / `debug`).
- [ ] The old stub message no longer appears for intentional ingestion attempts.
- [ ] Ingestion success and basic failure cases are handled gracefully.
- [ ] Tests pass and cover the new behavior.
- [ ] Scope was respected (no major redesign of graph state or specialist logic).

---

## Follow-up Items (Add to TODO if not already present)

- Add proper validation for ingested records (beyond minimum viable fields).
- Consider whether ingestion should trigger any enrichment or specialist work.
- Revisit whether a machine-readable status or error categorization is needed for ingestion failures.

**Do not expand scope beyond designing and implementing a clean ingestion flow.** If the design discussion reveals the need for larger changes, document them as follow-ups rather than implementing them now.
# Task: Refactor Supervisor to Act as Pure Coordinator / Router

**Created:** 2026-06-02

**Objective:** Refactor `src/agents/supervisor.py` so that it behaves strictly as a coordinator and router, in line with the architectural principles in `docs/architecture.md`. The supervisor should no longer act as a data owner or direct accessor of storage.

**References:**
- `docs/architecture.md` — "Core Architectural Philosophy (Phase 1+)" section
- Current `src/agents/supervisor.py` (still contains direct `get_storage()`, `find_person`, and `upsert_person` calls)
- Recent work: Minimal `PersonResponse` (1912), Ingestion redesign (1000), subsequent cleanup tasks

---

## Current State vs. Desired State

**Current reality (as of June 2026):**
- The supervisor directly calls `storage.find_person()`.
- The supervisor directly calls `storage.upsert_person()` (during successful ingestion).
- It contains a large amount of response construction logic and decision-making about data presence.
- It still returns internal `person` objects in the graph state in several places.

**Desired behavior (per architecture):**
- The **Supervisor** is a **coordinator and router**, not a data owner or direct accessor.
- It should detect the type of request, decide which specialist (or core storage) should handle it, and route accordingly.
- Even basic identity resolution may eventually need to be delegated rather than done via direct database calls.
- The supervisor should remain narrow and explicit.

---

## Scope for This Task

**In scope:**
- Refactor `supervisor_agent` to reduce or eliminate direct storage access where feasible.
- Move data access responsibilities (find/upsert) into more appropriate places (could be dedicated storage helper functions, or preparation for future specialist agents).
- Reduce the amount of business logic inside the supervisor for constructing responses.
- Keep the existing graph flow (supervisor → enrich → validator → supervisor for ingestion) working.
- Update any comments, docstrings, and `MyceliumGraphState` usage as needed to reflect the new responsibilities.

**Out of scope (for this iteration):**
- Fully eliminating all direct storage access (we do not yet have specialist agents for identity).
- Redesigning the overall graph structure or adding new node types.
- Implementing true specialist agent spawning or routing (that can come later).
- Changing the public `PersonResponse` shape.

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file to `prompts/cursor/in-progress/`.

2. **Analyze current responsibilities**
   - Catalog exactly what data-related decisions and operations currently live inside `supervisor_agent`.
   - Identify which operations could reasonably be delegated or moved (even if not fully eliminated yet).

3. **Design the refactored structure**
   - Propose a cleaner separation of concerns.
   - Consider introducing thin helper modules or functions for data access (e.g., a `core_identity` module or storage facade) that the supervisor can call, rather than reaching directly into `get_storage()`.
   - Document the proposed shape in your `output.md`.

4. **Implement the refactor**
   - Refactor `supervisor.py` according to the design.
   - Update `MyceliumGraphState` usage if the internal contract changes.
   - Keep all existing functionality working (lookups, non-core attribute detection, ingestion flow).

5. **Update tests and documentation**
   - Ensure all existing tests continue to pass.
   - Update any comments or architecture notes that describe the supervisor’s role.
   - Optionally add a short note in `docs/architecture.md` about the progress toward the coordinator model.

6. **Deliver artifacts**
   - Follow the standard done-folder process.
   - Update `TODO.md` to mark this item complete and note any remaining gaps.

---

## Success Criteria

- [ ] The supervisor no longer performs direct `find_person` / `upsert_person` calls in its main logic (or they are isolated behind clear delegation points).
- [ ] The supervisor’s primary responsibility is routing and coordination rather than data manipulation.
- [ ] All existing functionality (lookup, non-core requests, ingestion) continues to work without behavioral changes.
- [ ] The codebase better reflects the architectural principle that the supervisor is a coordinator/router.
- [ ] Tests pass and the change is reviewable.

---

## Follow-up Items (to be added to TODO.md)

- Continue reducing direct data access as specialist agents are introduced.
- Evaluate whether core identity resolution should eventually be handled by a dedicated "Core Identity" specialist rather than direct storage.
- Further narrow the supervisor’s response construction logic.

**This is a significant but focused refactor.** Keep the changes reviewable. If the ideal design requires larger structural changes, document them clearly as follow-ups rather than forcing them into this task.
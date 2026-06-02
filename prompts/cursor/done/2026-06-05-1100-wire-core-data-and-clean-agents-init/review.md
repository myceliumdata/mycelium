# Review: Task 1100 — Wire the core_data_agent into the graph and clean agents/__init__.py (and any remaining ingest wiring)

**Reviewer:** Grok (planning/reviews role)  
**Date:** 2026-06-05 (review performed on uncommitted Cursor output)  
**Task artifacts:** `prompt.md`, `output.md` (no prior review.md)  
**Related commits (historical context):** 1070 simplified the graph; 1100 focused on package surface.

---

## Objective Recap (from prompt)
- Wire `core_data_agent` node (from 1060) into the active graph.
- Update supervisor routing decision so queries flow through the specialist.
- Clean `src/agents/__init__.py`: remove `enrich_agent`/`validator_agent` exports; add/export only `core_data_agent` + `supervisor_agent`.
- Legacy enrich/validator/person_prep files stay on disk (reserved for future internal add work).
- Verify `get_core_graph()` + `run_query()` still work.
- Do **not** touch tests or docs (delegated to other tasks, e.g. 1080/1090/1110).

---

## Changes Delivered
### `src/agents/__init__.py` (the primary delta for this task)
```diff
-"""Specialist and supervisor agent nodes."""
+"""Active LangGraph agent nodes for the query-only public interface."""

 from agents.core_data import core_data_agent
-from agents.enrich import enrich_agent
 from agents.supervisor import supervisor_agent
-from agents.validator import validator_agent

-__all__ = ["core_data_agent", "enrich_agent", "supervisor_agent", "validator_agent"]
+__all__ = ["core_data_agent", "supervisor_agent"]
```
- Docstring updated to reflect query-only active surface.
- Matches the "Required Output" request for diffs.

### `src/graphs/core.py`
- No changes in this task (correctly noted in output.md).
- Wiring was completed in 1070: `START → supervisor → core_data → END` (with `_route_after_supervisor` conditional on `state.route == "core_data"`).
- Imports: direct from `agents.core_data` and `agents.supervisor` (plus the package `__all__` now aligns).

### Supervisor behavior (post-1070/1100)
- `supervisor_agent` is now a pure thin coordinator:
  ```python
  return {
      "route": "core_data",
      "audit_log": [
          "Supervisor: evaluating query.",
          "Supervisor: routing to core_data specialist.",
      ],
  }
  ```
- No storage access, no response building, no ingest logic. Matches "supervisor as coordinator" in `docs/architecture.md`.

### Core data specialist (owns the work)
- `core_data_agent` (async, uses `asyncio.to_thread` for sync lookup):
  - Delegates to `CoreIdentity.find_by_key`.
  - Uses `responses.py` builders (`response_found`, `response_not_found`, `response_non_core`).
  - Populates `response`, `person` (when present), `audit_log`.
  - Handles `requested_attributes` → non-core deferral via `non_core_attributes()`.
- `CoreIdentity` (facade over `storage.core`) provides `find_by_key` + `persist` (persist ready for future internal use).

---

## Verification Performed
1. **Linter & Tests** (run in current tree state):
   - `uv run ruff check src tests` → **All checks passed!**
   - `uv run pytest -q` → **22 passed** (includes `test_graph_invokes_supervisor_then_core_data`, core_data_agent unit tests, run_query behaviors, supervisor route test).

2. **CLI smoke**:
   - `uv run mycelium query --person-key "Nichanan Kesonpat"`
   - Result: 1 result with correct core fields, "Found core record..." message, debug tags, `trace_id` + `thread_id`, and LangSmith URL. Exit code appropriate.

3. **MCP smoke**:
   - `from mycelium_mcp.server import query_person, list_specialist_routing`
   - `query_person(...)` for real person returns results len=1. Tools surface is query-only.

4. **Graph structure & package surface**:
   - Direct import `from agents import core_data_agent, supervisor_agent` succeeds.
   - `build_core_graph()` / `get_core_graph()` produces nodes including "supervisor" and "core_data".
   - End-to-end `run_query` exercises `supervisor` (audit: "routing to core_data") then `core_data_agent` (audit: "CoreDataAgent: lookup...").
   - `graphs/core.py` eager singleton + async checkpointer + trace capture all intact.

5. **Scope & dead-code hygiene**:
   - No active `from ... import enrich_agent` etc. in `src/` outside the legacy files themselves (and generated egg-info).
   - `src/main.py` and `src/mycelium_mcp/server.py` are already query-only (no ingest/`provided_data`).
   - Legacy files (`enrich.py`, `validator.py`, `person_prep.py`) remain on disk but are **not imported** by the active graph or package `__init__`.
   - `routing.py` (and `evaluate_supervisor_turn`) is not called by the current supervisor or core_data path (only by its own test file).

6. **Code inspection**:
   - `src/agents/core_data.py`, `supervisor.py`, `graphs/core.py`, `models/state.py`, `storage/core.py` all align with the "query-only, supervisor routes to core_data specialist" model.
   - `Person`, `PersonQuery`, `PersonResponse`, `MyceliumGraphState.route` (now `Literal["core_data"] | None`) are minimal and correct.

---

## Findings & Assessment

**Approved — task complete and correct.**

**Strengths:**
- Precise scope adherence (only the requested wiring confirmation + `__init__` cleanup; left docs/tests alone).
- Supervisor is now convincingly narrow (the 1100/1070 refactor delivered the philosophy).
- Specialist owns its data access + response shaping — no god-agent behavior.
- All smoke paths (CLI direct, graph ainvoke, MCP) and the dedicated path test pass cleanly.
- Output.md accurately described the state ("Already wired from task 1070"; this task = package surface + verification).

**Minor observations (not blockers for this task; surface for 1110 final-cleanup):**
1. **Stale references in docs/TODO** (expected):
   - `TODO.md`: "Wire `core_data_agent` into graph; supervisor routes to it (`1070`, `1100`)." is still unchecked.
   - `docs/architecture.md`: still says "Wiring supervisor → `core_data_agent` in the graph is in progress...; today routing still performs lookups inline inside the supervisor path."
   - 1110 prompt already calls for aligning these + removing any remaining public ingest refs.

2. **routing.py is now effectively dead in the active path**:
   - Contains `evaluate_supervisor_turn` + `SupervisorDecision` that duplicate the classification/lookup/response logic now inside `core_data_agent` + `responses.py`.
   - Only imported/used by `tests/test_supervisor_routing.py` (which also tests the new thin `supervisor_agent`).
   - Architecture doc still calls out `src/agents/routing.py` as the classifier.
   - Safe to leave for now (per scope), but 1110 or a dedicated note should decide: delete, deprecate, or keep as "shared decision helper for future specialists".

3. **Legacy state fields**:
   - `MyceliumGraphState` still carries `validation_passed`, `validation_errors` (and `person_prep` etc. logic in other files). Unused in query flow. Again, final cleanup territory.

4. **Generated artifacts**:
   - `src/mycelium.egg-info/` is stale (still lists old agents in SOURCES/PKG-INFO). Will be refreshed on `uv pip install -e .` or build. Not a functional issue.

5. **History noise**:
   - Several review commits appear in `git log` for prior tasks (e.g. repeated "Review task 1080"). Not introduced by this task.

**No scope violations found.** Cursor correctly claimed (via the done/ dir presence), executed narrowly, verified the required items, and produced clear output.

---

## Recommendation
- **Merge / accept the task output.** The implementation matches the prompt, architecture direction, and "Phase 1 MVP — Strictly Minimal Core" rules.
- Create the 1110 follow-up work (already in `prompts/cursor/next/`) to perform the global search for stragglers, run the final verification matrix, and update TODO + architecture.md.
- Optionally: after 1110 lands, consider whether `routing.py` should be removed or kept with a clear "historical / test-only" header.
- Once 1110 is also reviewed and landed, the migration to "queries only, core owned by CoreDataAgent" can be called complete.

**Project is now in the desired post-1100 state for the active query path.**

(If any adjustments to this review or the artifacts are needed, reply with specifics and I will iterate or spawn a targeted follow-up prompt.)

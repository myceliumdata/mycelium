# Task: Support multiple results for ambiguous names (e.g. Kevin Zhang) in core lookups

## Objective
Fix name-based lookups so that `person_key` matching multiple people (same name, different employers) returns *all* matching core records in `results` (instead of only the first one). This addresses the report that searching "Kevin Zhang" returns only one result even though the seed intentionally contains two distinct people with that name (Bain Capital Ventures and Upfront Ventures).

The `find_by_key` / storage lookup must now be able to return 0, 1, or N persons. Update the call sites, response builders, state, legacy routing, and relevant tests/docs to handle lists while preserving exact behavior for unique names.

## Constraints & Principles
- Keep changes small and reviewable.
- Preserve the query-only public surface, existing response shapes for single matches, the recent stabilization (sync checkpointer, recovery wrapper, health_check), and all prior behavior for unique keys.
- Do not introduce new Pydantic models for the multi case; the existing `PersonResponse.results` (list) already supports it.
- Update messages to be plural-aware when >1 match (e.g. "Found 2 core records for 'Kevin Zhang'.").
- For non-core attribute requests on an ambiguous key, return all matching core records + the "still researching" narrative (the attrs apply to the key).
- Follow "Prefer simplification".
- After changes, only run smoke tests by default (`uv run pytest -m smoke -q`).
- Strictly respect scope boundaries (listed below). If you believe something outside scope is required to keep the system working, stop immediately and document.
- Do not touch the health_check tool, the MYCELIUM_USE_SYNC_CHECKPOINTER logic, recovery in _run_mcp_query, or any legacy enrich/validator/person_prep beyond what's necessary for type compat in tests.
- References to `find_by_key` in docs should be updated only where they claim "one core dict".

## Context
- The seed was deliberately created with duplicate names for some people (see `prompts/cursor/done/2026-06-01-1730-process-raw-data-to-seed-crm/` review and prompt: "Kevin Zhang → both entries kept (no user rule)"). There are exactly two:
  - person-0058: Kevin Zhang, Bain Capital Ventures
  - person-0438: Kevin Zhang, Upfront Ventures
- Current lookup (`storage.find_person` + `CoreIdentity.find_by_key`) uses `fetchone()` + returns `Person | None`, so only the first match (Bain) is ever returned for name "Kevin Zhang".
- `PersonResponse.results` is already a list (supports 0/1/N). The builders `response_found`/`response_non_core` currently hardcode single-person lists.
- Active path: `core_data_agent` (in core_data.py) does the lookup and builds response (sets "person"/"persons" on payload).
- Legacy path (only for tests): `evaluate_supervisor_turn` in routing.py does similar.
- `MyceliumGraphState` has `person: Person | None`.
- CLI / MCP / run_query already consume `response.results` so will automatically benefit once lookup returns multiples.
- `CoreStorage` still uses singular for upsert/get_by_id (those stay single).
- Tests for core_data_agent and supervisor_routing use stubs that return single/None; not_found asserts "person" not in result.
- Docs claim single-result in tables/descriptions (architecture.md, full-code-walkthrough.md).
- This is a core data / identity resolution improvement. Per architecture, name-based resolution is still direct in core for Phase 1; full specialist disambiguation is future.

See:
- `data/seed_crm.json` for the two Kevin Zhang entries.
- `src/storage/core.py` (find_person, fetchone)
- `src/agents/core_identity.py`
- `src/agents/core_data.py` (the _build and _run functions)
- `src/agents/responses.py` (builders)
- `src/agents/routing.py` (legacy evaluate)
- `src/models/state.py`
- The two smoke test files for core_data and routing.
- `docs/architecture.md` (lookup table) and `docs/full-code-walkthrough.md`

Repro command: `uv run mycelium query --person-key "Kevin Zhang"`

Expected after fix: results list of length 2, containing both firms, message plural, debug with num_matches or similar.

## Exact Steps (perform in order)
1. **Claim the task (per WORKFLOW.md)**: Immediately move this file from `prompts/cursor/next/2026-06-06-mcp-handle-ambiguous-names.md` to `prompts/cursor/in-progress/2026-06-06-mcp-handle-ambiguous-names/prompt.md`. This is the lock. Document the move. Do not touch other files in in-progress/.

2. **Discovery & repro**:
   - Read the full list of files in scope (see boundaries).
   - Run the repro: `uv run mycelium query --person-key "Kevin Zhang"` (should currently show only 1 result).
   - Confirm the two entries in `data/seed_crm.json`.
   - Run `uv run python -c "..."` or similar to count matches via storage directly if helpful.
   - Read `prompts/cursor/done/2026-06-01-1730-process-raw-data-to-seed-crm/review.md` (or prompt) to confirm intentional dup for Kevin Zhang.
   - Note current signatures and fetchone() vs fetchall().

3. **Implement (only in the allowed files)**:
   - `src/storage/core.py`:
     - Rename `find_person` to `find_persons` (or keep name but change return; prefer clear rename).
     - Change return type to `list[Person]`.
     - For id match: return [the_person] or [].
     - For name: use `.fetchall()` and list comp of _row_to_person.
     - Update docstring to note may return multiple for name matches.
     - Keep all other methods (upsert, get_by_id, seed etc.) unchanged.
   - `src/agents/core_identity.py`:
     - Update `find_by_key` to return `list[Person]`.
     - Delegate to storage.find_persons (update call).
     - Update docstring.
   - `src/agents/responses.py`:
     - Update `response_found(query, persons: list[Person], ...)` — build results = [p.core_dict() for p in persons], choose singular/plural message and debug (include num_matches).
     - Same for `response_non_core(query, persons: list[Person], attributes, ...)`.
     - not_found unchanged (still results=[]).
     - Update internal calls and docstrings.
   - `src/agents/core_data.py`:
     - Update `_build_lookup_response` to return `tuple[list[Person], PersonResponse, str]`.
     - Use `matches = core_identity.find_by_key(...)`.
     - if not matches: return [], not_found, "not_found"
     - For deferred and found: pass the full `matches` list to the (updated) response_ builders.
     - In `_run_core_data_lookup`: unpack matches, build payload with "persons": matches and "person": matches[0] if exactly 1 else None (for test/legacy compat).
     - Update logs, docstring, type hints.
   - `src/agents/routing.py` (legacy, only tests use it):
     - Update `SupervisorDecision` dataclass: add `persons: list[Person] = field(default_factory=list)`, keep `person` for compat.
     - In `evaluate_supervisor_turn`: use `persons = ...find_by_key()`
     - if not: return decision with response=not_found (no person)
     - else: pass `persons` list to response_*, set persons=persons, person= first only if len==1.
     - Import field if needed.
     - Update docstrings.
   - `src/models/state.py`:
     - Add `persons: list[Person] = Field(default_factory=list)` to `MyceliumGraphState`.
     - Keep `person: Person | None = None` (for compat in tests/legacy; first match when exactly one).
     - Update class docstring to explain persons for name ambiguity.
   - `tests/test_core_data_agent.py` and `tests/test_supervisor_routing.py`:
     - Update the `_StubCoreIdentity.find_by_key` overrides to return `list[Person]` ( [self._person] if present else [] ).
     - The existing asserts on result["person"] and "person" not in should continue to work because core_data still sets "person" for the single-person test cases.
     - Optionally add a quick smoke for multi but not required (keep smoke-only; do not add full tests unless classified).
   - `docs/architecture.md`:
     - Update the lookup table row: change "results: one core dict" to "results: one or more core dicts (multiple when name is ambiguous)" and note plural message.
   - `docs/full-code-walkthrough.md`:
     - Update any descriptions that say "results: one core dict" or assume single lookup result for names (search for relevant sections around core_data, find_by_key, lookup flow).

4. **Verification (smoke by default)**:
   - `uv run pytest -m smoke -q` (must pass, include output).
   - Repro the user issue: `uv run mycelium query --person-key "Kevin Zhang"` — must now return exactly 2 results, both firms present, message mentions 2 / "core records", debug updated.
   - Test non-core attrs too: `uv run mycelium query --person-key "Kevin Zhang" --attributes email` — should return 2 cores + "still researching" message.
   - Test unique name still works as before (e.g. "Nichanan Kesonpat" returns 1, singular message).
   - Test not-found still works.
   - Manual python smoke for the agent if desired (using the pattern in prompt).
   - Confirm no linter errors on changed files: `uv run ruff check <the files>`.
   - Confirm module imports and CLI/MCP entrypoints still work.

5. **Output artifacts**:
   - Move the claimed prompt into `prompts/cursor/done/2026-06-06-mcp-handle-ambiguous-names/prompt.md`
   - Create `.../output.md` with: summary of changes + decisions (e.g. why list[Person], plural messages, compat "person" field), the diff or key edits, full output of all verification commands you ran, open questions/follow-ups (e.g. whether to add a real multi-name test, update TODO, docs elsewhere).
   - Remove *only* your claimed file from in-progress/.
   - You may leave a placeholder review.md but it is not required.

6. **Process**:
   - Follow claiming, only-your-file cleanup, smoke policy, and "stop and escalate" exactly (see WORKFLOW.md and the .cursor rule).
   - If you need to edit a file outside the scope list below to "make it work", **stop**, document the problem clearly in output.md + review-notes.md, do not make the change, and instead create a follow-up prompt in next/.

## Scope Boundaries (Strict)
You may **only** modify files under these paths:
- `src/storage/core.py`
- `src/agents/core_identity.py`
- `src/agents/core_data.py`
- `src/agents/routing.py`
- `src/agents/responses.py`
- `src/models/state.py`
- `tests/test_core_data_agent.py`
- `tests/test_supervisor_routing.py`
- `docs/architecture.md`
- `docs/full-code-walkthrough.md`

**Out of Scope (Do Not Touch)**
- `src/mycelium_mcp/server.py` (except if needed for import compat — avoid)
- `src/main.py`
- `src/graphs/core.py`
- Any other src/agents/* (enrich, validator, person_prep, supervisor.py — the active supervisor doesn't do lookup)
- `tests/` other than the two listed
- `README.md`, `TODO.md`, `prompts/resets/`, `bin/`, `data/`, `pyproject.toml`, etc.
- Do not add new test files or change test markers without explicit Grok classification in advance.
- Do not modify the health_check tool or any stabilization logic.

If you determine changes outside this list are necessary:
- Stop immediately.
- Document the exact problem in your `output.md` and any review-notes.md.
- Do not make the out-of-scope edit.
- Create a follow-up prompt in `prompts/cursor/next/` describing the additional work.

This rule is mandatory.

## Test Execution Policy
- Default: only `uv run pytest -m smoke -q`.
- The existing smoke tests for core_data_agent and routing must continue to pass (they use single-person stubs).
- If you add or significantly change a test, stop and document; Grok will determine smoke vs full category. Full tests (real DB, run_query, graph) must be run immediately with correct marker.
- Do not add full-suite tests for this task unless necessary (prefer updating the stub-based smoke tests minimally).

## Required Output & Artifacts
- Exactly as in WORKFLOW.md: the done/ subdir with prompt.md + output.md (and optional review.md).
- Your output.md must include the verification command outputs (especially the "Kevin Zhang" query showing 2 results + the smoke pytest).

Follow the full claiming process in `prompts/cursor/WORKFLOW.md` and `.cursor/rules/04-cursor-workflow.mdc` before any implementation.

## Suggested Acceptance Criteria (for later review)
- `uv run mycelium query --person-key "Kevin Zhang"` returns 2 results with both employers and a plural message.
- Same for non-core attrs request on the key.
- Unique names unchanged (1 result, singular message).
- All smoke tests pass.
- Scope respected, no other files edited.
- Docs updated where they described single-result assumption.
- Artifacts complete and process followed.


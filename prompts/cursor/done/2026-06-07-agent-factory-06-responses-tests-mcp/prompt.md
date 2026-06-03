# Task: Agent Factory Phase 2 - Slice 06: Responses + core_data propagation + full test fixtures + integration + mcp list (optional polish)

**Read these first (mandatory):**
- `docs/plans/agent-factory-phase2.md` (the approved plan - focus on observability, success criteria involving debug/audit, "Generated code is clean, committed, and follows project style")
- The detailed implementation plan at `docs/plans/agent-factory-phase2.md` (focus on "## Updates to Graph, State, Dispatch, Responses, Core Data (Minimal but Necessary)" for responses + core_data, Step 6, "Verification (End-to-End + Regression)" full matrix especially non_core + "via", temp_storage fixture updates, mcp polish note, and Step 6 verification)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`
- `prompts/system/CORE_PROMPT.md`

**Objective**
Update `src/agents/responses.py` (add specialist: str | None = None param to response_non_core (and optionally others), conditional message tweak "... researching {attr_list} (via {specialist})." + debug entry when present; keep backward compat). Update `src/agents/core_data.py` (pass specialist="core_data" at the response_* call sites in _build_lookup_response). Update `tests/conftest.py` and `tests/test_core_graph.py` temp_storage fixture (add monkeypatch.setenv for MYCELIUM_AGENT_REGISTRY_PATH and MYCELIUM_SPECIALISTS_DIR to tmp paths; call reset_agent_registry() and reset_agent_factory() in setup/teardown; keep the existing 4 resets + envs). Enhance the non_core full test assertions (still "still researching", classifications present, now expect specialist name in debug or via the narrative for the attr's category). Run full targeted tests. Polish (small): update `src/mycelium_mcp/server.py` list_specialist_routing to actually use get_agent_registry().list_agents() and return a useful dict with specialists (update its docstring from "Phase 1 stub").

This slice delivers the propagation + full test isolation + basic observability for specialists. Polish is optional if small.

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. Prioritize getting basic creation + registration + dynamic loading + routing working cleanly before any polish (LLM refine, advanced storage logic, etc.). Strictly enforce auto_commit=False + temporary paths in all tests. Real git commits only happen on actual (non-test) runs. Generated agents must always include the prominent AUTO-GENERATED header and be committed to git on real usage."

**Extra Guidance from Paul**
Prioritize simplicity. If a slice feels complex, simplify the implementation and document it. Generated code must always have the full AUTO-GENERATED header. Tests must never trigger real git commits.

For this slice: small param + 2 call sites in core_data; fixture updates are mechanical copy of the CATEGORIES_PATH pattern from Phase 1; mcp polish only if it fits as tiny diff; tests use the tmp envs + resets from prior slices.

**Constraints & Principles**
- Strictly limited scope (see box below).
- Changes must match the approved plan's notes for responses/core_data/fixture (small + consistent with classifications propagation from Phase 1).
- Small, reviewable change only.
- Smoke -q default; full targeted for graph/non_core.
- This is slice 06 of the small sequence.

**Context**
- Slices 01-05 have the factory + trigger + dispatch (creation works in test mode, routing to specialist now possible).
- The approved plan has the notes for responses (specialist= kwarg), core_data (pass "core_data"), the temp_storage updates (add the two new envs + resets), the non_core test enhancement, and the mcp list_specialist_routing polish.
- Current responses pass classifications; core_data includes them in payload and calls response_non_core for deferred.
- The full verification matrix in the plan (manual creation + "via", isolation with envs, restart load, git hygiene, observability in audit/debug/state.route, mcp list real) is the target for this slice's verif.
- Later: only 07 polish/refine/final.

See approved plan updates section, Step 6, Verification matrix, and Success Criteria (observability, "via" in narrative).

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, select the oldest (this one), **immediately move** it to `prompts/cursor/in-progress/2026-06-07-agent-factory-06-responses-tests-mcp/prompt.md` (or the exact name). Only then begin work. Document the move in your output.md. Never work on a file still in next/.

2. **Discovery (read-only)**: 
   - Read the approved plan sections listed above. Read the current responses.py (response_non_core and debug_for_query), core_data.py (_build_lookup_response and the response calls), test_core_graph.py (temp_storage fixture and test_query_non_core_attributes), conftest.py, mcp/server.py (list_specialist_routing stub).
   - Run `git status`, `uv run pytest -m smoke -q`, `uv run pytest -m full -q -k "non_core or query_non_core" ` (baseline).
   - Run a manual non-core: `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes age,x_handle` (note current "still researching", classifications in debug, no "via" yet).
   - Confirm no MYCELIUM_AGENT_* envs in use yet.

3. **Update `src/agents/responses.py`** (small per plan):
   - Add specialist: str | None = None to the signature of response_non_core (and for symmetry to response_found / response_not_found if it fits small).
   - In the message construction for non_core: if specialist and specialist != "core_data": use f"... we're still researching {attr_list} (via {specialist})." else the original.
   - In debug_for_query calls inside the builders: include **({"specialist": specialist} if specialist else {}) if passed.
   - Keep default=None for zero breakage on existing calls.

4. **Update `src/agents/core_data.py`** (small per plan):
   - In _build_lookup_response (or the call sites for the three response_*), pass specialist="core_data" to the response_non_core / response_not_found / response_found calls (alongside the existing **id_kwargs, **clf_kwargs).
   - In the payload in _run_core_data_lookup, it already includes classifications; no other change.

5. **Update `tests/conftest.py`**:
   - Add `from agents.registry import reset_agent_registry`
   - Add `from agents.factory import reset_agent_factory` (if the factory has reset state).
   - Include reset_agent_registry (and reset_agent_factory) in the cleanup tuple.

6. **Update `tests/test_core_graph.py` temp_storage fixture and test**:
   - In the fixture: after the existing resets and monkeypatches (including CATEGORIES_PATH), add:
     monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(tmp_path / "agent_registry.json"))
     monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
     from agents.registry import reset_agent_registry
     from agents.factory import reset_agent_factory
     reset_agent_registry()
     reset_agent_factory()
   - In the teardown (yield after): also call the new resets.
   - Enhance `test_query_non_core_attributes` (or add assert): still assert "still researching" and classifications in debug; now also assert the specialist name appears (e.g. "demographic" or "via demographic_specialist" or in the debug classifications for "age").
   - Keep other tests (existing/missing, plain dicts) passing.

7. **Run full relevant tests**:
   - `uv run pytest -m full -q -k "non_core or query_non_core or supervisor or graph or factory or registry"`

8. **Polish (optional, only if small diff)**:
   - Update `src/mycelium_mcp/server.py` list_specialist_routing:
     - _bootstrap()
     - reg = get_agent_registry()  # import
     - specialists = [ {"name": n, "category": e.category, "is_generated": e.is_generated, "storage_path": e.storage_path} for n, e in reg._data.agents.items() ] or similar from list_agents()
     - return json.dumps( {"message": "Specialist agent routing is coordinated by the supervisor via the Agent Registry (Phase 2).", "specialists": specialists }, indent=2 )
   - Update its docstring from "Phase 1 stub..." to note Phase 2.
   - Update any test that calls it (in test_mcp or similar) if the output shape changes (keep compatible if possible).

9. **Verification (smoke + full + manual per plan)**:
   - `uv run pytest -m smoke -q`
   - `uv run pytest -m full -q -k "non_core or query_non_core or supervisor_agent or graph or factory or registry"`
   - `uv run ruff check` on the touched files (responses, core_data, conftest, test_core_graph, mcp if polished).
   - Manual matrix from plan (core query; non-core that exercises dispatch + a specialist (may create in real run, which is intended and will commit the generated + registry + data/agents/ for the cat; check audit has "created..." + "routing to ...specialist", response still "researching" but with (via XXX) if polished, debug has specialist, results core, git log --oneline -1 shows the auto commit with header in the py; subsequent query no re-create; ls data/agents/<cat>/ ; python -c reset + get_fn + call; isolation env create; delete reg reseed; header grep; mcp list now real if polished; observability; lint).
   - `git status` after manual (the artifacts from real creation are committed as required).

10. **Output artifacts (exactly per WORKFLOW)**:
    - Create `prompts/cursor/done/2026-06-07-agent-factory-06-responses-tests-mcp/output.md` with summary ( "followed lightweight: small param + calls + fixture copy of pattern; mcp polish only because tiny"; decisions), git diff --stat + key (the specialist= in responses, fixture envs), **explicit `git diff --stat` for conftest.py and test_core_graph.py + Guard compliance statement**, full verif outputs (incl. the creation manual outputs + git log), scope confirmation (only listed files), open Qs (e.g. "ready for 07?").
    - Move/copy this prompt into the done/ dir as `prompt.md`.
    - Remove **only** the file you claimed from `prompts/cursor/in-progress/`.

11. **Process hygiene**:
    - Follow claiming exactly.
    - Stop on scope (no changes to factory beyond what's already, no new tests beyond fixture, no architecture.md, no real changes outside listed even if "to make tests pass").
    - Do not touch the approved plan.

**Guard against excessive insertions in shared files (mandatory):**
This series prioritizes small, reviewable slices. Shared test files (especially `tests/test_supervisor_routing.py`, `tests/conftest.py`, `tests/test_core_graph.py`) are high-risk for scope creep because prior phases may have left them in varying states.

When the scope includes modifying a shared test file:
- ONLY perform the *exact fixture updates + test enhancements* explicitly described in the "Exact Steps" for *this* slice.
- Make the *absolute minimum* changes (e.g. adding the two envs + two reset calls to the temp_storage fixture *as described*; one targeted enhancement to the non_core test assertion).
- Run ruff *only* on lines you added. Revert unrelated hunks.
- **Never** restore, re-add, expand, refactor, or clean up tests from other phases. If the file looks incomplete, document + `git diff --stat` in output.md and create a separate follow-up prompt instead of bloating this slice.

In output.md you **must** include:
- `git diff --stat <the test file(s)>`
- A statement: "Test/fixture changes strictly limited to the described updates. No unrelated restorations."

Large or unexplained insertions will be treated as a scope violation.

## Scope Boundaries (Strict)
You may only create or modify files under the following paths:
- `src/agents/responses.py`
- `src/agents/core_data.py`
- `tests/conftest.py` (the exact fixture updates described only — see Guard rule above)
- `tests/test_core_graph.py` (the exact fixture + one test enhancement described only — see Guard rule above)
- `src/mycelium_mcp/server.py` (only the list_specialist_routing function + docstring, if the polish fits as small)

**Out of Scope (Do Not Touch)**
- src/agents/dispatch.py, supervisor.py, graphs/core.py, models/state.py (already done in 05), src/agents/factory/*, src/agents/specialists/*, src/agents/registry.py, tests/test_supervisor_routing.py (beyond any incidental), docs/ (except running verif), pyproject.toml, the plan files, TODO.md, any other mcp functions, etc.
- Do not implement advanced storage or full refine (07).
- Do not make large changes to mcp (only the list function if small).

If you determine that changes outside this scope are necessary:
- **Stop immediately.**
- Clearly document the problem in your `output.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory.

## Test Execution Policy
- Default: `uv run pytest -m smoke -q`.
- For graph/non_core: the full targeted (`-m full -k "non_core or ... "`) as specified in the plan's Verification.
- Fixture updates must use the tmp envs + resets (enforce isolation per user's note).
- Any mcp test updates must stay smoke-compatible.

## Required Output Location & Artifacts
- `prompts/cursor/done/2026-06-07-agent-factory-06-responses-tests-mcp/output.md`
- The claimed prompt moved to the done/ subdir as `prompt.md`

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly before doing any implementation work.

## Suggested Acceptance (for Grok + Paul review)
After Cursor delivers, we will review the output.md, confirm only the listed files were touched ( + mcp if polished), re-run smoke + full non_core/graph + the full manual matrix from the plan (core query; non-core creation of e.g. financial via net_worth, check audit "created" + "routing to financial_specialist", "researching" + (via ) if, debug/classifications, git commit + header + data/agents/, subsequent, load after reset, isolation, mcp list real if, observability, lint), confirm "via" or specialist name surfaces, scope clean, add review.md if needed, then (if good) commit this small slice and prepare the final (07-polish-refine-verify).

Start by claiming the file (move to in-progress/). Good luck — make the change small, explicit, and reviewable. Reference the approved plan for every detail (exact updates, fixture pattern, verification matrix).

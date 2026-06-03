# Task: Agent Factory Phase 2 - Slice 05: Dispatch + graph wiring + state update + supervisor creation trigger + test adjustments

**Read these first (mandatory):**
- `docs/plans/agent-factory-phase2.md` (the approved plan - focus on "How the Supervisor will trigger agent creation (minimal changes)", "Keep Supervisor thin", Agent Generation & Lifecycle, High-Level Architecture)
- The detailed implementation plan at `docs/plans/agent-factory-phase2.md` (focus on "## How the Supervisor Will Trigger Agent Creation (Minimal Changes)" exact diff, "## Updates to Graph, State, Dispatch, Responses, Core Data (Minimal but Necessary)", the dispatch.py code, Step 5, and Step 5 verification commands)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`
- `prompts/system/CORE_PROMPT.md`

**Objective**
Create the tiny `src/agents/dispatch.py` (specialist_dispatcher). Update `src/models/state.py` (route: str | None = None + desc update). Update `src/graphs/core.py` (generalize Route/conditional/_route_after_supervisor, add "specialist" dispatch node + specialist_dispatcher, remove hardcoded core_data node, update docs/comments). Update `src/agents/supervisor.py` with the creation trigger block (exact from plan: after classify, if non-unknown ag and not has_agent then factory.create, set route=ag) + audit. Adjust tests in test_supervisor_routing.py (pre-register in the classifies test so route becomes the specialist name and assert updates; add new trigger test with tmp reg + monkeypatch on factory.create to verify trigger without side effects).

This slice delivers the dynamic routing + creation trigger. Minimal changes per directive.

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. Prioritize getting basic creation + registration + dynamic loading + routing working cleanly before any polish (LLM refine, advanced storage logic, etc.). Strictly enforce auto_commit=False + temporary paths in all tests. Real git commits only happen on actual (non-test) runs. Generated agents must always include the prominent AUTO-GENERATED header and be committed to git on real usage."

**Extra Guidance from Paul**
Prioritize simplicity. If a slice feels complex, simplify the implementation and document it. Generated code must always have the full AUTO-GENERATED header. Tests must never trigger real git commits.

For this slice: ~10-15 lines in supervisor, ~25 loc dispatch, small graph/state updates; tests use pre-register or monkeypatch + tmp to avoid real create/git.

**Constraints & Principles**
- Strictly limited scope (see box below).
- The supervisor diff, dispatch code, graph changes must match the approved plan's sections exactly (use the pasted diff/code).
- Small, reviewable change only.
- Smoke -q default.
- This is slice 05 of the small sequence.

**Context**
- Slices 01-04 have scaffold/registry/base/factory (with test mode creation).
- The approved plan has the exact supervisor diff (the Phase 2 block with reg = get_agent_registry(), if not has then factory.create_specialist( category=cat, agent_name=ag, description=..., llm_refine=False ), route = ag), the dispatch.py full, the state route change, the graph updates (Route, _route_after, build add_node specialist, conditional, docs), and the test adjustments (pre-register, new trigger test).
- Current: supervisor always "core_data", graph hardcoded core_data node + Literal, state route Literal.
- Later: responses/core_data for specialist= (06), full integration.

See approved plan "How the Supervisor Will Trigger...", the updates section, Step 5, and risks (supervisor thin).

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, select the oldest (this one), **immediately move** it to `prompts/cursor/in-progress/2026-06-07-agent-factory-05-dispatch-graph-supervisor/prompt.md` (or the exact name). Only then begin work. Document the move in your output.md. Never work on a file still in next/.

2. **Discovery (read-only)**: 
   - Read the approved plan sections listed above. Read the current supervisor.py (the Phase 1 comment and route=core_data), graphs/core.py (Route, _route_after, build nodes/edges), state.py (route Literal), test_supervisor_routing.py (the classifies test and route=="core_data" assert).
   - Run `git status`, `uv run pytest -m smoke -q`, `uv run mycelium query --person-key "Nichanan Kesonpat"` (baseline core only).
   - Note the current audit always has "routing to core_data specialist."

3. **Create `src/agents/dispatch.py`** (matching the approved code exactly):
   ```python
   """Specialist dispatcher (routes state.route to the registry fn). See approved plan Step 5."""
   from __future__ import annotations
   from typing import Any
   from models.state import MyceliumGraphState
   from agents.registry import get_agent_registry
   from agents.core_data import core_data_agent

   def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
       if isinstance(state, MyceliumGraphState):
           return state
       return MyceliumGraphState.model_validate(state)

   def specialist_dispatcher(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
       current = _coerce(state)
       target = current.route or "core_data"
       fn = get_agent_registry().get_agent_fn(target)
       if fn is None:
           fn = core_data_agent
       # Optional: audit "Dispatch: invoking {target}"
       return fn(current)
   ```

4. **Update `src/models/state.py`**:
   - Change `route: Literal["core_data"] | None = None` to `route: str | None = None`
   - Update the MyceliumGraphState docstring and the field description to "The target specialist name (e.g. \"core_data\", \"contact_specialist\"). Set by supervisor; used by dispatch to invoke the registered agent. Phase 2+ dynamic."

5. **Update `src/graphs/core.py`** (small targeted changes):
   - Route = str | Literal["__end__"] (or just use str for the conditional)
   - Update _route_after_supervisor: if current.route in (None, "__end__"): return "__end__" ; return "specialist"
   - In build_core_graph: import specialist_dispatcher from agents.dispatch
     - graph.add_node("specialist", specialist_dispatcher)
     - graph.add_conditional_edges( "supervisor", _route_after_supervisor, {"specialist": "specialist", "__end__": END}, )
     - Remove the "core_data" node and the old add_edge("core_data", END)
   - Update all comments, docstrings, Route type, run_query docs that assumed hardcoded "core_data" (e.g. "supervisor routes to core_data" -> "supervisor sets route; dispatch invokes the registered specialist (core_data or generated)").
   - Keep the checkpointer/eager init logic unchanged.

6. **Update `src/agents/supervisor.py`** (the minimal trigger per plan):
   - Add imports: from agents.factory import get_agent_factory ; from agents.registry import get_agent_registry
   - Replace the Phase 1 comment + route = "core_data" block with the exact diff from plan:
     ```python
     # Phase 2: use classification to pick a real specialist. Create on demand if needed.
     route = "core_data"
     if classifications:
         for cl in classifications:
             cat = cl.get("category")
             ag = cl.get("assigned_agent")
             if cat and cat != "unknown" and ag and ag != "core_data":
                 reg = get_agent_registry()
                 if not reg.has_agent(ag):
                     factory = get_agent_factory()
                     factory.create_specialist(
                         category=cat,
                         agent_name=ag,
                         description=cl.get("description") or f"Data related to {cat}.",
                         examples=[],
                         llm_refine=False,
                         # auto_commit is True in real runs; tests isolate via env + pytest guard inside factory
                     )
                 route = ag
                 break
     ```
   - Optionally add audit: if the create happened, append "Supervisor: created new specialist {ag} for category {cat}."
   - Update the module docstring and the old "Phase 1: ..." comment.
   - Keep _coerce and the classify loop unchanged.

7. **Update tests in `tests/test_supervisor_routing.py`**:
   - In the existing test_supervisor_agent_classifies_requested_attributes: pre-register the contact_specialist (using reg = get_agent_registry(); reg.register_agent({"name": "contact_specialist", "category": "contact", ... "is_generated": False}, save=False) before the supervisor_agent call, so has_agent true -> route becomes "contact_specialist"; update the assert result["route"] == "contact_specialist" and the audit "routing to contact_specialist".
   - Add a new @pytest.mark.smoke test_supervisor_triggers_creation_for_unregistered_specialist (use monkeypatch.setenv for MYCELIUM_AGENT_REGISTRY_PATH to a tmp that has only core_data, reset_agent_registry, monkeypatch the factory.create_specialist to a fake that records calls and returns {"created":True...}, build state with requested_attributes=["email"], call supervisor_agent, assert len(calls)==1 and calls[0]["agent_name"]=="contact_specialist", result["route"] == "contact_specialist").

8. **Verification (smoke + manual for this slice)**:
   - `uv run pytest -m smoke -q`
   - `uv run mycelium query --person-key "Nichanan Kesonpat"` (core only, still works).
   - Note: non-core queries will now hit the trigger (full isolation in slice 06).
   - `git status` (changes limited to dispatch.py, state.py, graphs/core.py, supervisor.py, test_supervisor_routing.py).
   - `uv run ruff check` on those files.
   - Confirm via `git diff --stat tests/test_supervisor_routing.py` that changes were only the described pre-register update + new trigger test (per Guard rule).
   - Confirm the classifies test now asserts the specialist route (because pre-registered), the new trigger test passes without side effects.

9. **Output artifacts (exactly per WORKFLOW)**:
   - Create `prompts/cursor/done/2026-06-07-agent-factory-05-dispatch-graph-supervisor/output.md` with summary (decisions: "minimal diff in supervisor as specified; dispatch is the thin abstraction; tests avoid real creation via pre-register/monkeypatch+tmp"), git diff --stat + key diffs (the supervisor trigger block), **explicit `git diff --stat` for the test file + statement that test changes were limited per the Guard rule**, full verif outputs, scope confirmation, open Qs.
   - Move/copy this prompt into the done/ dir as `prompt.md`.
   - Remove **only** the file you claimed from `prompts/cursor/in-progress/`.

10. **Process hygiene**:
    - Follow claiming exactly.
    - Stop on scope (do not update responses/core_data yet, no mcp, no architecture.md, no real creation that commits in this run, no changes to factory tests or base).
    - Do not touch the approved plan.

## Scope Boundaries (Strict)
You may only create or modify files under the following paths:
- `src/agents/dispatch.py`
- `src/models/state.py`
- `src/graphs/core.py`
- `src/agents/supervisor.py`
- `tests/test_supervisor_routing.py` (the **listed test adjustments only** — see the Guard rule above; no unrelated test code)

**Out of Scope (Do Not Touch)**
- src/agents/responses.py, src/agents/core_data.py, src/agents/factory/* (beyond import/use), src/agents/specialists/*, src/agents/registry.py (beyond import/use), src/mycelium_mcp/server.py, tests/test_core_graph.py, tests/conftest.py, docs/ (except running verif commands), data/, pyproject.toml, the plan files, TODO.md, any real generated .py or data/agents/ in source tree, git commits from tests.

If you determine that changes outside this scope are necessary:
- **Stop immediately.**
- Clearly document the problem in your `output.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory.

## Test Execution Policy
- Default: `uv run pytest -m smoke -q` only.
- The trigger test must use tmp reg + monkeypatch (no real create, no git, no pollution).
- The classifies test update uses pre-register (save=False) to keep smoke.
- No full tests in this slice.

**Guard against excessive insertions in shared files (mandatory):**
This series prioritizes small, reviewable slices. Shared test files (especially `tests/test_supervisor_routing.py`, `tests/conftest.py`, `tests/test_core_graph.py`) are high-risk for scope creep because prior phases may have left them in varying states.

When the scope includes modifying a shared test file:
- ONLY perform the *exact test adjustments* explicitly described in the "Exact Steps" for *this* slice (e.g. "in the existing X test: do Y; add a new Z test with W").
- Make the *absolute minimum* changes required (pre-register calls or monkeypatches *only as described*, inside the relevant test or as minimal fixture tweak if explicitly called for).
- Run ruff *only* on lines you added. Revert unrelated hunks.
- **Never** restore, re-add, expand, refactor, or clean up tests from other phases. If the file looks incomplete, document + `git diff --stat` in output.md and create a separate follow-up prompt instead of bloating this slice.

In output.md you **must** include:
- `git diff --stat <the test file(s)>`
- A statement: "Test changes strictly limited to the described adjustments + minimal support. No unrelated restorations."

Large or unexplained insertions will be treated as a scope violation.

## Required Output Location & Artifacts
- `prompts/cursor/done/2026-06-07-agent-factory-05-dispatch-graph-supervisor/output.md`
- The claimed prompt moved to the done/ subdir as `prompt.md`

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly before doing any implementation work.

## Suggested Acceptance (for Grok + Paul review)
After Cursor delivers, we will review the output.md, confirm only the 5 files were touched, re-run smoke (classifies test now sees specialist route + updated assert; new trigger test records create call and sets route correctly), manual core query still clean, git status limited to scope, the supervisor diff and dispatch wiring match the plan exactly, scope clean, add review.md if needed, then (if good) commit this small slice and prepare the next (06-responses-tests-mcp).

Start by claiming the file (move to in-progress/). Good luck — make the change small, explicit, and reviewable. Reference the approved plan for every detail (exact diff, dispatch code, test updates).

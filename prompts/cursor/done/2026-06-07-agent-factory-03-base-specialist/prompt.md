# Task: Agent Factory Phase 2 - Slice 03: Base SpecialistStorage (full, with strategy hooks)

**Read these first (mandatory):**
- `docs/plans/agent-factory-phase2.md` (the approved plan - the immutable source of truth for vision, core requirements, architecture components (Base Specialist), risks, success criteria, "clear architectural hooks so agents can later autonomously evolve their own backing store")
- The detailed implementation plan at `docs/plans/agent-factory-phase2.md` (focus on "### Base Specialist (src/agents/specialists/base.py)" full code + docstrings, Step 3, risks "Future storage intelligence hooks missing or weak", "Proposed Final File/Folder Structure", and Step 3 verification commands)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md` (thin supervisor as coordinator/router only, specialists own domains + storage strategy, small/reviewable changes, scope discipline, no god-agents)
- `prompts/system/CORE_PROMPT.md` (explicit orchestration, narrow responsibilities, Python 3.12+/Pydantic, small increments, reference architecture + core prompt)

**Objective**
Implement the complete SpecialistStorage in base.py per the approved detailed plan design (atomic writes using tempfile+os.replace, _ensure_initialized that writes both json files with the exact initial shapes from the plan, load/save, get_strategy/current_strategy, migrate_to stub with the long explanatory comment for future agent-owned evolution). Update specialists/__init__.py. Add smoke test using tmp dir. No wiring or creation yet.

This slice delivers the storage helper + hooks. Follow lightweight: full but simple, reuse atomic pattern from Phase 1.

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. Prioritize getting basic creation + registration + dynamic loading + routing working cleanly before any polish (LLM refine, advanced storage logic, etc.). Strictly enforce auto_commit=False + temporary paths in all tests. Real git commits only happen on actual (non-test) runs. Generated agents must always include the prominent AUTO-GENERATED header and be committed to git on real usage."

**Extra Guidance from Paul**
Prioritize simplicity. If a slice feels complex, simplify the implementation and document it. Generated code must always have the full AUTO-GENERATED header. Tests must never trigger real git commits.

For this slice: full storage helper + hooks now; no migration impl yet (stub + comments only); tests use tmp.

**Constraints & Principles**
- Strictly limited scope (see box below).
- The implementation must match the sketches in the approved plan's "Base Specialist" section exactly (copy the full class, the exact strategy and initial storage dicts, the migrate_to error message).
- Small, reviewable change only.
- Smoke -q default.
- This is slice 03 of the small sequence.

**Context**
- Slice 01/02 have the skeleton and registry.
- The approved plan has the exact SpecialistStorage class (including _atomic_write, _ensure_initialized with the strategy json having "flat_json_v1" + upgrade_path, the migrate_to NotImplemented with the comment about "the specialist .py itself (being editable committed source)").
- Current patterns to reuse: atomic from classification/engine.py _save; singleton not needed here (per-agent instances); env in base for MYCELIUM_AGENT_DATA_DIR.
- Later slices will use SpecialistStorage in the factory (04) and generated agents (04+).

See approved plan "Base Specialist" design, "Risk / Mitigation" (future storage intelligence), and Step 3 verification.

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, select the oldest (this one), **immediately move** it to `prompts/cursor/in-progress/2026-06-07-agent-factory-03-base-specialist/prompt.md` (or the exact name). Only then begin work. Document the move in your output.md. Never work on a file still in next/.

2. **Discovery (read-only)**: 
   - Read the approved plan sections listed above. Read the current base.py stub from slice 01.
   - Run `git status` and `ls data/agents/ 2>/dev/null || echo "no data/agents yet (expected)"` to confirm current state.
   - Run `uv run pytest -m smoke -q` to baseline.
   - Confirm no data/agents/ subtree yet.

3. **Implement full `src/agents/specialists/base.py`** (matching the approved "Base Specialist" design exactly):
   - Use the full code from the plan's design section for class SpecialistStorage (imports json os tempfile datetime timezone Path Any; the _slug, __init__, _ensure_initialized with the exact strategy dict and initial storage dict, _atomic_write with tempfile + os.replace + cleanup, load, save (updates last_updated), get_strategy, current_strategy, migrate_to with the full docstring and raise NotImplementedError message referencing "the specialist .py itself (being editable committed source) can grow the intelligence...").
   - Add module docstring: """Base for generated specialists. Provides storage helper + future upgrade hooks (see approved plan)."""
   - Keep any existing stub comments updated to "Implemented per approved plan Step 3."

4. **Update `src/agents/specialists/__init__.py`** to the final:
   ```python
   """Specialist base and generated agents (Phase 2 Agent Factory - see approved plan)."""
   from .base import SpecialistStorage
   __all__ = ["SpecialistStorage"]
   ```

5. **Add smoke test in `tests/test_supervisor_routing.py`** (or alongside existing):
   - Add the test from plan Step 3 (using tempfile + SpecialistStorage("demo", base_dir=Path(d)) ; asserts on load (has "records"), save, get_strategy has "flat_json_v1").
   - Mark @pytest.mark.smoke

6. **Verification (smoke + manual for this slice)**:
   - `uv run pytest -m smoke -q`
   - Manual from approved Step 3:
     `uv run python -c '
     from agents.specialists.base import SpecialistStorage
     import tempfile
     from pathlib import Path
     d = tempfile.mkdtemp()
     s = SpecialistStorage("demo", base_dir=Path(d))
     data = s.load()
     print("initial records:", "records" in data)
     s.save({"records": {"p1": {"email": "a@b"}}})
     print("after save:", s.load()["records"]["p1"])
     st = s.get_strategy()
     print("strategy:", st["strategy"])
     print("migrate test (should raise):")
     try:
       s.migrate_to("minisql_v1")
     except NotImplementedError as e:
       print("raised as expected:", str(e)[:100])
     '`
   - `git status` (should show exactly changes in base.py + __init__.py + the test file).
   - `uv run ruff check src/agents/specialists/base.py src/agents/specialists/__init__.py tests/test_supervisor_routing.py`
   - Confirm no other files touched (in particular no data/agents/ created in source tree, only in the manual /tmp).

7. **Output artifacts (exactly per WORKFLOW)**:
   - Create `prompts/cursor/done/2026-06-07-agent-factory-03-base-specialist/output.md` with:
     - Summary of what was done and decisions (e.g. "followed lightweight: exact copy of SpecialistStorage from plan; atomic write reused from classification; test uses tmp only").
     - The diffs or `git diff --stat` + key new file contents (the migrate_to comment especially).
     - Full output of all verification commands.
     - Confirmation scope respected (only the 3 items).
     - Any open questions (e.g. "ready for slice 04?").
   - Move/copy this prompt into the done/ dir as `prompt.md`.
   - Remove **only** the file you claimed from `prompts/cursor/in-progress/`.
   - Optionally create review.md placeholder.

8. **Process hygiene**:
   - Follow claiming exactly.
   - If you feel you must edit outside the scope box to "make it work", **stop immediately**, document in output.md, and create a follow-up prompt instead of making the change.
   - Do not touch the approved plan.
   - Do not implement any creation, factory, registry changes, supervisor, graph, responses, or real data/agents/ in source.

## Scope Boundaries (Strict)
You may only create or modify files under the following paths:
- `src/agents/specialists/base.py`
- `src/agents/specialists/__init__.py`
- `tests/test_supervisor_routing.py` (the test addition **only** — see the new "Guard against excessive insertions" rule above)

**Out of Scope (Do Not Touch)**
- data/ (except reading; no creation in source tree), src/agents/factory/*, src/agents/registry.py, src/agents/dispatch.py, src/agents/supervisor.py, src/graphs/core.py, src/models/state.py, src/agents/core_data.py, src/agents/responses.py, src/agents/classification/*, src/mycelium_mcp/*, tests/test_core_graph.py, docs/ (except running verification commands), the plan files, TODO.md, or anything else.
- Do not create any data/agents/ in the source tree or run any creation that would trigger git or real files outside /tmp in manual.
- Do not implement any logic beyond the storage helper.
- Do not make large or unrelated changes to any test file (see Guard rule).

If you determine that changes outside this scope are necessary to keep the system working:
- **Stop immediately.**
- Clearly document the problem in your `output.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory. Violating scope boundaries will be treated as a failure to follow instructions.

## Test Execution Policy
- Default: `uv run pytest -m smoke -q` only.
- The storage test is smoke (pure, tmp dir, no DB/graph/creation).
- No full marker tests in this slice.

**Guard against excessive insertions in shared files (mandatory):**
This series prioritizes small, reviewable slices. Shared test files (especially `tests/test_supervisor_routing.py`, `tests/conftest.py`, `tests/test_core_graph.py`) are high-risk for scope creep because prior phases may have left them in varying states.

When the scope includes modifying a shared test file:
- ONLY add the *exact new @pytest.mark.smoke test function(s)* explicitly described in the "Exact Steps" for *this* slice.
- Make the *absolute minimum* one- or few-line supporting changes required for your *new test(s)* to run in isolation (e.g. monkeypatch/env *inside the body of your new test*, or a fixture update *only if the prompt explicitly instructs it for this slice*).
- Run ruff *only* on lines you personally added. Revert any unrelated hunks from `ruff --fix`.
- **Never** restore, re-add, expand, refactor, or clean up tests from other phases (classification, legacy routing, etc.). If the file looks incomplete or tests appear missing, document the observation + exact `git diff --stat` in output.md **and create a separate follow-up prompt** for test restoration/hygiene instead of bloating this slice.

In output.md you **must** include:
- `git diff --stat <the test file(s)>` for every modified test file.
- A statement: "Test insertions strictly limited to the new smoke test(s) + minimal required support (X lines added). No unrelated restorations or refactors from other phases."

Large or unexplained insertions in shared test files will be treated as a scope violation during review.

## Required Output Location & Artifacts
- `prompts/cursor/done/2026-06-07-agent-factory-03-base-specialist/output.md`
- The claimed prompt moved to the done/ subdir as `prompt.md`

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly before doing any implementation work.

## Suggested Acceptance (for Grok + Paul review)
After Cursor delivers, we will review the output.md, confirm only the 3 files were touched, **confirm via `git diff --stat tests/test_supervisor_routing.py` that test insertions were minimal and limited to the new smoke test + tiny support (per the Guard rule)**, re-run the verification commands (smoke + the manual tmp creation + cat jsons + migrate raise + git status limited to scope), confirm the base.py matches the approved plan design exactly (atomic, initial shapes, strategy, migrate_to comment about editable committed source), confirm no behavior change and no source tree pollution, add review.md if needed, then (if good) commit this small slice and prepare the next small prompt (04-agent-factory).

Start by claiming the file (move to in-progress/). Good luck — make the change small, explicit, and reviewable. Reference the approved plan for every detail.

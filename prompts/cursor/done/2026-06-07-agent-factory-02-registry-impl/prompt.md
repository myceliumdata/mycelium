# Task: Agent Factory Phase 2 - Slice 02: Registry implementation + singletons + load logic + basic tests

**Read these first (mandatory):**
- `docs/plans/agent-factory-phase2.md` (the approved plan - the immutable source of truth for vision, core requirements, architecture components (Agent Registry), risks, success criteria)
- The detailed implementation plan at `docs/plans/agent-factory-phase2.md` (or the session plan; focus on "Agent Registry (src/agents/registry.py + data/agent_registry.json)" full design section, Step 2, "Proposed Final File/Folder Structure", risks around import/collision/name safety, "Risk / Mitigation", and Step 2 verification commands)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md` (thin supervisor as coordinator/router only, specialists own domains + storage strategy, small/reviewable changes, scope discipline, no god-agents)
- `prompts/system/CORE_PROMPT.md` (explicit orchestration, narrow responsibilities, Python 3.12+/Pydantic, small increments, reference architecture + core prompt)

**Objective**
Implement the full AgentRegistry (the in-memory + persistent source of truth for specialists) per the approved detailed plan's "Agent Registry" design section. This includes Pydantic models (or equivalent), atomic load/save matching classification/engine.py pattern exactly, _SEED_REGISTRY (exact match to the json from slice 01), env MYCELIUM_AGENT_REGISTRY_PATH, has_agent/get_agent_fn (with core_data special case + file-spec load support for MYCELIUM_SPECIALISTS_DIR), register/list, and the module singletons get_/reset_agent_registry(). Update conftest and add/update smoke tests. No creation or supervisor changes yet.

This slice delivers a fully functional (but not yet wired) registry. Follow lightweight: reuse patterns exactly from Phase 1 classification/storage. No polish.

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. Prioritize getting basic creation + registration + dynamic loading + routing working cleanly before any polish (LLM refine, advanced storage logic, etc.). Strictly enforce auto_commit=False + temporary paths in all tests. Real git commits only happen on actual (non-test) runs. Generated agents must always include the prominent AUTO-GENERATED header and be committed to git on real usage."

**Extra Guidance from Paul**
Prioritize simplicity. If a slice feels complex, simplify the implementation and document it. Generated code must always have the full AUTO-GENERATED header. Tests must never trigger real git commits.

For this slice: implement the core registry logic + basic tests only; no factory, no base storage details beyond what's needed for stubs, no git, no dynamic specialist creation.

**Constraints & Principles**
- Strictly limited scope (see box below).
- Implementation must match the sketches in the approved plan's "Agent Registry" section exactly (copy the RegisteredAgent/AgentRegistryData shapes, the _load_agent_fn, the seed, the atomic _save, the singleton pattern).
- Small, reviewable change only.
- Smoke -q default.
- This is slice 02 of the small sequence.

**Context**
- Slice 01 created the data/agent_registry.json seed (core_data only) and the registry.py stub.
- The approved plan has the exact models, _load_agent_fn code, _SEED, singleton/get/reset, and the test verification (python -c with env for registry, has/get/list, smoke in test_supervisor_routing.py).
- Current patterns to reuse: singleton + reset from agents/classification/engine.py, src/storage/core.py, src/agents/core_identity.py, src/graphs/core.py; atomic _save from classification/engine.py; env MYCELIUM_* from all.
- Later slices will use the registry in factory (04), dispatch (05), supervisor trigger (05).

See approved plan "Agent Registry" design, "Risk / Mitigation" (import/collision, restart), and Step 2 verification.

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, select the oldest (this one), **immediately move** it to `prompts/cursor/in-progress/2026-06-07-agent-factory-02-registry-impl/prompt.md` (or the exact name). Only then begin work. Document the move in your output.md. Never work on a file still in next/.

2. **Discovery (read-only)**: 
   - Read the approved plan sections listed above. Read the current registry.py stub and data/agent_registry.json from slice 01 to see the stubs.
   - Run `git status` and `ls data/ src/agents/ ` to confirm current state.
   - Run `uv run pytest -m smoke -q` to baseline.
   - Confirm the seed json from slice 01.

3. **Implement full src/agents/registry.py** (matching the approved "Agent Registry" design exactly):
   - Add the necessary imports (from datetime import datetime; from pydantic import BaseModel, Field; from typing import Any, Callable; import json, os, tempfile, importlib, importlib.util, sys; from pathlib import Path).
   - The RegisteredAgent and AgentRegistryData Pydantic models exact from the plan's "Agent Registry" design section (including docstrings).
   - AgentRegistry class with:
     - __init__(self, registry_path: Path | None = None)
     - _default_registry_path() using os.getenv("MYCELIUM_AGENT_REGISTRY_PATH", "data/agent_registry.json")
     - _load(self) -> None : if exists json load + model_validate else seed + save
     - _save(self) -> None : atomic via tempfile.mkstemp + os.replace , exact copy of the pattern from src/agents/classification/engine.py _save
     - _create_seed(self) -> AgentRegistryData : return AgentRegistryData.model_validate(_SEED_REGISTRY)
     - reload, has_agent(name: str) -> bool, get_agent_fn(name: str) -> Callable[[Any], dict] | None (the full _load_agent_fn with core special-case + specialists_dir file spec load using MYCELIUM_SPECIALISTS_DIR), register_agent(entry: dict | RegisteredAgent, *, save: bool = True), list_agents() -> list[dict]
   - The _SEED_REGISTRY constant that produces identical data to the committed data/agent_registry.json from slice 01 (copy the json dict from plan).
   - Module level _agent_registry: AgentRegistry | None = None
   - def get_agent_registry() -> AgentRegistry: global ... if None: = AgentRegistry() ; return
   - def reset_agent_registry() -> None: global ... = None
   - Add clear comments: "See approved plan 'Agent Registry' design. Core special-cased for no file dep. File-spec load supports test isolation via MYCELIUM_SPECIALISTS_DIR (used in factory tests). Atomic save per Phase 1 classification pattern."

4. **Update tests/conftest.py**: Add `from agents.registry import reset_agent_registry` and include reset_agent_registry in the cleanup tuple (after reset_category_tree).

5. **Update/add smoke tests in tests/test_supervisor_routing.py** (or minimal new addition): 
   - Update existing if needed to keep passing.
   - Add a @pytest.mark.smoke test that exercises the registry (using tmp path via monkeypatch for isolation):
     ```python
     @pytest.mark.smoke
     def test_agent_registry_seeds_core_and_loads_fn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
         from agents.registry import get_agent_registry, reset_agent_registry
         monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(tmp_path / "reg.json"))
         reset_agent_registry()
         r = get_agent_registry()
         assert r.has_agent("core_data")
         fn = r.get_agent_fn("core_data")
         assert callable(fn)
         assert "core_data" in [a["name"] for a in r.list_agents()]
     ```
   - Add another for register to tmp.

6. **Verification (smoke + manual for this slice)**:
   - `uv run pytest -m smoke -q`
   - The manual from approved Step 2:
     `MYCELIUM_AGENT_REGISTRY_PATH=/tmp/test-reg-$$.json uv run python -c '
     from agents.registry import get_agent_registry, reset_agent_registry
     reset_agent_registry()
     r = get_agent_registry()
     print(r.has_agent("core_data"))
     print(r.list_agents())
     fn = r.get_agent_fn("core_data")
     print(fn)
     '`
   - `git status` (should show exactly the changes in registry.py, conftest.py, test_supervisor_routing.py).
   - `uv run ruff check src/agents/registry.py tests/conftest.py tests/test_supervisor_routing.py`
   - Confirm no other files touched, existing supervisor classify tests still pass (route still core_data in their asserts for now).

7. **Output artifacts (exactly per WORKFLOW)**:
   - Create `prompts/cursor/done/2026-06-07-agent-factory-02-registry-impl/output.md` with:
     - Summary of what was done and decisions (e.g. "followed lightweight by implementing exact from plan design; reused atomic pattern from classification; tests use tmp + env for isolation").
     - The diffs or `git diff --stat` + key new file contents (the registry.py key methods).
     - Full output of all verification commands.
     - Confirmation scope respected (only the 3 items).
     - Any open questions (e.g. "ready for slice 03?").
   - Move/copy this prompt into the done/ dir as `prompt.md`.
   - Remove **only** the file you claimed from `prompts/cursor/in-progress/`.
   - Optionally create review.md placeholder.

8. **Process hygiene**:
   - Follow claiming exactly.
   - If you feel you must edit outside the scope box to "make it work", **stop immediately**, document in output.md, and create a follow-up prompt instead of making the change.
   - Do not touch the approved plan.
   - Do not implement any creation, factory, base, dispatch, supervisor, graph, responses, or real data/agents/.

## Scope Boundaries (Strict)
You may only create or modify files under the following paths:
- `src/agents/registry.py`
- `tests/conftest.py`
- `tests/test_supervisor_routing.py`

**Out of Scope (Do Not Touch)**
- data/ (except reading the seed from 01), src/agents/factory/*, src/agents/specialists/*, src/agents/dispatch.py, src/agents/supervisor.py, src/graphs/core.py, src/models/state.py, src/agents/core_data.py, src/agents/responses.py, src/agents/classification/*, src/mycelium_mcp/*, tests/test_core_graph.py, docs/ (except running verification commands), the plan files, TODO.md, or anything else.
- Do not implement any real creation logic or wire to supervisor/state/graph (that is slice 05).
- Do not run full tests.

If you determine that changes outside this scope are necessary to keep the system working:
- **Stop immediately.**
- Clearly document the problem in your `output.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory. Violating scope boundaries will be treated as a failure to follow instructions.

## Test Execution Policy
- Default: `uv run pytest -m smoke -q` only.
- The new/updated tests here must be @pytest.mark.smoke (use tmp_path + env for isolation; no real graph or creation).
- No full marker tests in this slice.

## Required Output Location & Artifacts
- `prompts/cursor/done/2026-06-07-agent-factory-02-registry-impl/output.md`
- The claimed prompt moved to the done/ subdir as `prompt.md`

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly before doing any implementation work.

## Suggested Acceptance (for Grok + Paul review)
After Cursor delivers, we will review the output.md, confirm only the 3 files were touched, re-run the verification commands (smoke + the env python -c + git status limited to scope), confirm the registry matches the approved plan design exactly (has/get/list for core_data, load fn works, seed roundtrips via model), confirm no behavior change to existing supervisor tests, add review.md if needed, then (if good) commit this small slice and prepare the next small prompt (03-base-specialist).

Start by claiming the file (move to in-progress/). Good luck — make the change small, explicit, and reviewable. Reference the approved plan for every detail.

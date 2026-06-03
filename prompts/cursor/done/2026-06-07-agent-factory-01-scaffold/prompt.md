# Task: Agent Factory Phase 2 - Slice 01: Scaffold + seed registry + jinja2 + basic package structure

**Read these first (mandatory):**
- `docs/plans/agent-factory-phase2.md` (the approved high-level plan - the immutable source of truth for vision, core requirements, architecture components, risks, success criteria)
- `docs/plans/agent-factory-phase2-plan.md` (the detailed implementation plan if published; key excerpts for Step 1, seed JSON, file list, and lightweight notes are reproduced below for self-containment. The full detailed plan was approved in the Grok session.)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md` (thin supervisor as coordinator/router only, specialists own domains + storage strategy, small/reviewable changes, scope discipline, no god-agents)
- `prompts/system/CORE_PROMPT.md` (explicit orchestration, narrow responsibilities, Python 3.12+/Pydantic, small increments, reference architecture + core prompt)

**Objective**
Perform exactly Step 1 of the approved detailed plan (Scaffold + seed registry + jinja2 + package dirs + stubs): 
- Add the jinja2 dependency via `uv add jinja2`.
- Create the committed `data/agent_registry.json` with the exact initial seed (version 1.0, only the core_data entry as specified).
- Create the directory structure and minimal stub files for the new modules (registry.py, factory subpackage with __init__ + agent_factory.py + templates/ containing a basic .j2 placeholder, specialists subpackage with __init__ + base.py stub, dispatch.py stub).
- Zero logic, zero wiring, zero behavior change to existing code. Pure addition of structure and seed data. This sets up the subsequent small slices (02-registry, 03-base, 04-factory+template, etc.).

This is the first of a sequence of small, sequential, reviewable slices (modeled on the successful 7-slice classify-0x series). Each slice is independently reviewable and commit-able.

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. Prioritize getting basic creation + registration + dynamic loading + routing working cleanly before any polish (LLM refine, advanced storage logic, etc.). Strictly enforce auto_commit=False + temporary paths in all tests. Real git commits only happen on actual (non-test) runs. Generated agents must always include the prominent AUTO-GENERATED header and be committed to git on real usage."

**Extra Guidance from Paul**
Prioritize simplicity. If a slice feels complex, simplify the implementation and document it. Generated code must always have the full AUTO-GENERATED header. Tests must never trigger real git commits.

For **this slice**: stubs only (no real methods, no jinja rendering, no atomic save logic yet, no git commit code, no singleton wiring that affects runtime). Use the simplest possible stubs. Do not implement any part of Step 2+.

**Constraints & Principles**
- Strictly limited scope (see box below).
- Reference and align with the approved high-level (agent-factory-phase2.md) and the detailed plan's Step 1 description, seed, and "Proposed Final File/Folder Structure".
- No changes to existing source (supervisor, graphs, state, core_data, responses, classification, mcp, main, storage, etc.), tests, docs (except running verification commands), or any generated specialist files.
- Small, reviewable change only. One logical group per slice.
- Follow "Prefer simplification and deletion over adding new abstractions."
- After implementation, only run smoke tests (`uv run pytest -m smoke -q`).
- The prompt for Cursor must follow the claiming process in WORKFLOW.md exactly.
- Real git commits of generated agents only on non-test runs (enforced in later slices via auto_commit + pytest guard).

**Context**
- The approved high-level `docs/plans/agent-factory-phase2.md` defines the components (Agent Factory in src/agents/factory/, Agent Registry at data/agent_registry.json, Base Specialist, specialists/ dir, Jinja2 + optional LLM, git commit of generated agents, storage per category with strategy.json hooks, supervisor triggers creation with minimal changes, keep supervisor thin).
- The detailed implementation plan (approved) breaks it into 7 small slices with exact verification. Step 1 is pure scaffold.
- Current state (confirmed via prior exploration): no agent_registry.json, no data/agents/, no src/agents/registry.py, no factory/ or specialists/ dirs, no jinja2 in pyproject, supervisor always routes to core_data, graph is hardcoded to core_data node.
- This slice is the first in the sequence. Later slices will fill logic (02 for registry full impl, 03 base storage, 04 factory render+create+git, 05 dispatch+graph+supervisor trigger, 06 responses+tests+fixtures, 07 refine+polish+final verify).
- The large planning work happened in the Grok session; this is the first executable Cursor task from it. Do not work on any superseded planning artifacts.

See the approved detailed plan (Step 1 section, "Proposed Final File/Folder Structure", "Agent Registry" design for the exact seed, verification commands) for full details. Key excerpts for this slice are inline below.

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, select the oldest matching this slice, **immediately move** it to `prompts/cursor/in-progress/2026-06-07-agent-factory-01-scaffold/prompt.md` (create the subdir if needed). Only then begin work. Document the move and timestamp in your output.md. Never work on a file still in next/. If in-progress has other files, leave them alone.

2. **Discovery (read-only)**: 
   - Read the approved `docs/plans/agent-factory-phase2.md` (focus on High-Level Architecture, Design Decisions, Short Summary of High-Level Steps, Risks, Success Criteria, and "Next Steps After Approval").
   - Read the relevant sections of the detailed implementation plan for Step 1 (Proposed Final File/Folder Structure, the exact seed for agent_registry.json, the lightweight priority, verification commands for Step 1).
   - Read `docs/architecture.md` (sections on Supervisor as coordinator, Derivative/Non-Core Data, Current Phase Focus, Working Principles).
   - Run `git status`, `ls -R data/ src/agents/ | head -30` to confirm current state (no agent_registry.json, no agents/ under data, no registry/factory/specialists under src/agents/).
   - Confirm jinja2 is absent: `uv run python -c "import jinja2" || echo "jinja2 not present (expected)"`.

3. **Add the dependency (controlled)**:
   - Run `uv add jinja2` (this updates pyproject.toml and uv.lock with the new runtime dependency; this is the approved way per the plan).

4. **Create the seed registry data (exact content)**:
   - Create `data/agent_registry.json` with **exactly** this content (must match the _SEED_REGISTRY constant that will be added in a later slice; version 1.0, last_updated as shown, only the core_data entry):

```json
{
  "version": "1.0",
  "last_updated": "2026-06-03T00:00:00+00:00",
  "agents": {
    "core_data": {
      "name": "core_data",
      "category": "core",
      "description": "Core identity (id, name, employer) — the always-present fallback specialist.",
      "module_path": "agents.core_data",
      "entrypoint": "core_data_agent",
      "storage_path": null,
      "strategy_path": null,
      "is_generated": false,
      "created_at": null
    }
  }
}
```

   - `git add data/agent_registry.json`.

5. **Scaffold the package directories and stub files (stubs only)**:
   - Create directories: `src/agents/specialists/`, `src/agents/factory/templates/`.
   - Create `src/agents/specialists/__init__.py` (minimal):
     ```python
     """Specialist base and generated agents (Phase 2 Agent Factory - see approved plan)."""
     from .base import SpecialistStorage
     __all__ = ["SpecialistStorage"]
     ```
   - Create `src/agents/specialists/base.py` (stub only - full SpecialistStorage in slice 03):
     ```python
     """Base for generated specialists. Provides storage helper + future upgrade hooks (see approved plan Step 3 + design)."""
     from pathlib import Path
     from typing import Any

     class SpecialistStorage:
         """Stub. Real implementation (atomic JSON + strategy.json + migrate_to hook) comes in slice 03."""
         def __init__(self, category: str, base_dir: Path | None = None) -> None:
             self.category = category
             # TODO in slice 03: ensure dirs, write initial storage.json + storage_strategy.json, implement load/save/get_strategy/migrate_to

         def load(self) -> dict[str, Any]:
             return {"records": {}}

         def save(self, data: dict[str, Any]) -> None:
             pass

         def get_strategy(self) -> dict[str, Any]:
             return {"strategy": "flat_json_v1"}
     ```
   - Create `src/agents/registry.py` (stub only - full impl in slice 02):
     ```python
     """Agent Registry (data/agent_registry.json + in-memory). See approved plan for full design (Step 2)."""
     from pathlib import Path
     from typing import Any, Callable

     # TODO slice 02: Pydantic models or equivalent, AgentRegistry class with atomic load/save,
     # _SEED_REGISTRY (must produce identical to the committed data/agent_registry.json),
     # _default using MYCELIUM_AGENT_REGISTRY_PATH, has_agent, get_agent_fn (core special case + file spec),
     # register, list, singletons get_agent_registry / reset_agent_registry.

     def get_agent_registry():
         # Stub: later will return real registry that knows core_data
         class _Stub:
             def has_agent(self, name: str) -> bool:
                 return name == "core_data"
             def get_agent_fn(self, name: str) -> Callable | None:
                 if name == "core_data":
                     from agents.core_data import core_data_agent
                     return core_data_agent
                 return None
             def list_agents(self):
                 return [{"name": "core_data", "category": "core"}]
         return _Stub()

     def reset_agent_registry() -> None:
         pass
     ```
   - Create `src/agents/factory/__init__.py` (empty or minimal pass).
   - Create `src/agents/factory/agent_factory.py` (stub only - full in slice 04):
     ```python
     """Agent Factory (Jinja2 templates + generation + git commit + dynamic registration).
     See approved plan Step 4 for full design and create_specialist contract."""
     from pathlib import Path
     from typing import Any

     # TODO slice 04: jinja2.Environment, AgentFactory class, create_specialist (validate, render, write py with header,
     # init SpecialistStorage for the cat, update registry, dynamic load, auto_commit handling, _commit_artifacts via subprocess),
     # optional _refine_with_llm stub, singletons get_agent_factory / reset.

     class AgentFactory:
         def create_specialist(self, category: str, agent_name: str, description: str, examples: list[str] | None = None, *, llm_refine: bool = False, auto_commit: bool = True) -> dict[str, Any]:
             # Stub for slice 01. Real creation + commit + load in slice 04.
             return {"created": False, "reason": "stub - implemented in slice 04"}

     def get_agent_factory():
         return AgentFactory()

     def reset_agent_factory() -> None:
         pass
     ```
   - Create `src/agents/factory/templates/specialist_agent.py.j2` (placeholder - full template body in slice 04):
     ```jinja2
     """{{ agent_name }} — auto-generated specialist for category "{{ category }}".

     AUTO-GENERATED by Agent Factory on {{ created_at }}.
     (Full template body with SpecialistStorage usage, _coerce, {{ agent_name }} fn, response builders,
     and storage hooks will be filled in slice 04 per the approved detailed plan design section.)
     See approved plan for the exact target rendered code and jinja variables.
     """
     # Placeholder - do not use for execution yet.
     ```
   - Create `src/agents/dispatch.py` (stub only - real dispatcher in slice 05):
     ```python
     """Specialist dispatcher (routes state.route to the registry fn). See approved plan Step 5."""
     from typing import Any

     def specialist_dispatcher(state: Any) -> dict:
         # Stub. Real impl (lookup route in registry, call the fn, fallback to core_data) in slice 05.
         from agents.core_data import core_data_agent
         # For now just delegate to core_data so existing behavior is untouched.
         if isinstance(state, dict):
             from models.state import MyceliumGraphState
             state = MyceliumGraphState.model_validate(state)
         return core_data_agent(state)
     ```

6. **Verification (smoke only, no behavior change)**:
   - `uv run pytest -m smoke -q` (must stay completely green; nothing broken).
   - `git status` (should show exactly: modified pyproject.toml + uv.lock, new data/agent_registry.json, and the new stub files under src/agents/registry.py + src/agents/factory/ + src/agents/specialists/ + src/agents/dispatch.py).
   - `cat data/agent_registry.json | head -30` (confirm exact seed with only core_data).
   - `uv run python -c '
import jinja2
print("jinja2 version:", jinja2.__version__)
import json, pprint
data = json.load(open("data/agent_registry.json"))
pprint.pprint(list(data["agents"].keys()))
print("registry seed ok")
from agents.registry import get_agent_registry, reset_agent_registry
reset_agent_registry()
r = get_agent_registry()
print("has core_data:", r.has_agent("core_data"))
print("list:", r.list_agents())
fn = r.get_agent_fn("core_data")
print("core_data fn callable:", callable(fn))
print("factory import ok")
from agents.factory import get_agent_factory
print("factory stub:", get_agent_factory().create_specialist("test", "test_specialist", "desc", auto_commit=False))
print("dispatch import ok")
from agents.dispatch import specialist_dispatcher
print("dispatch stub ok")
from agents.specialists.base import SpecialistStorage
print("base stub ok")
' ` (confirm all new modules import, registry seeds correctly, stubs return expected no-op shapes, jinja2 is importable).
   - `ls -R src/agents/specialists src/agents/factory data/agents 2>/dev/null | cat` (confirm structure; data/agents/ should be absent or empty since no real creation yet).

7. **Output artifacts (exactly per WORKFLOW.md)**:
   - Create `prompts/cursor/done/2026-06-07-agent-factory-01-scaffold/output.md` with:
     - Summary of what was done and decisions (e.g. "followed lightweight: pure stubs, no logic, exact seed from plan, uv add for dep, simple .j2 placeholder").
     - `git diff --stat` + key excerpts of new files (especially the registry.json seed and one stub).
     - Full output of all verification commands above.
     - Confirmation that scope was respected (only the listed files + dep update).
     - Any open questions (e.g. "ready for slice 02-registry impl?").
   - Move/copy this prompt into the done/ dir as `prompt.md`.
   - Remove **only** the file you claimed from `prompts/cursor/in-progress/`.
   - Optionally create a review.md placeholder.

8. **Process hygiene**:
   - Follow claiming exactly (move before any edits).
   - If you feel you must edit outside the scope box to "make it work", **stop immediately**, document in output.md, and create a follow-up prompt instead of making the change.
   - Do not implement any real registry logic, factory creation, template rendering, storage init, git commit, dispatch, or touch supervisor/graph/state/tests/responses.
   - Do not run full tests (`-m full`), only smoke.
   - Do not touch the approved plans, TODO.md, architecture.md (except reads), or any existing code.
   - Do not create any real specialist .py or data/agents/ subdirs (that happens on real create in later slices).

## Scope Boundaries (Strict)
You may only create or modify files under the following paths:
- `pyproject.toml` (and the resulting uv.lock from `uv add`)
- `data/agent_registry.json`
- `src/agents/registry.py`
- `src/agents/dispatch.py`
- `src/agents/factory/__init__.py`
- `src/agents/factory/agent_factory.py`
- `src/agents/factory/templates/specialist_agent.py.j2`
- `src/agents/specialists/__init__.py`
- `src/agents/specialists/base.py`

**Out of Scope (Do Not Touch)**
- Any file under `src/models/`, `src/agents/supervisor.py`, `src/agents/core_data.py`, `src/agents/responses.py`, `src/agents/classification/`, `src/graphs/`, `src/mycelium_mcp/`, `src/main.py`, `src/storage/`, `tests/`, `docs/` (except reading the approved plans and running verification commands), `prompts/cursor/in-progress/` (other files), the approved plan files themselves, TODO.md, or anything else.
- Do not implement real methods, jinja rendering, atomic writes, git calls, singletons that affect runtime behavior, or any creation/routing logic.
- Do not create data/agents/ directories or any *_specialist.py files.
- Do not modify existing behavior or run queries that would trigger creation.

If you determine that changes outside this scope are necessary:
- **Stop immediately.**
- Clearly document the problem in your `output.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory. Violating scope boundaries will be treated as a failure to follow instructions.

## Test Execution Policy
- Default: `uv run pytest -m smoke -q` only.
- No new tests required in this slice (test_agent_factory.py and updates to existing tests come in slices 04 and 06).
- If you feel a test is needed for the stubs, stop and document; Grok will decide (prefer no new tests here).

## Required Output Location & Artifacts
- `prompts/cursor/done/2026-06-07-agent-factory-01-scaffold/output.md`
- The claimed prompt moved to the done/ subdir as `prompt.md`

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly before doing any implementation work.

## Suggested Acceptance (for Grok + Paul review)
After Cursor delivers, we will review the output.md, confirm only the allowed files + dep update were touched, re-run the full verification matrix from the prompt, confirm the registry seed matches exactly, confirm all stubs import and the smoke tests remain green with zero behavior change, add review.md if needed, then (if good) commit this small slice and ask for the next small prompt (02-registry).

Start by claiming the file (move to in-progress/ as the subdir containing prompt.md). Good luck — make the change small, explicit, lightweight, and reviewable. Reference the approved plans for every detail (exact seed, stub expectations, verification). Do not proceed beyond this slice.
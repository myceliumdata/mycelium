# Review: Task 2026-06-07-agent-factory-05-dispatch-graph-supervisor — Dispatch + graph wiring + state update + supervisor creation trigger + test adjustments (Agent Factory Phase 2, Step 5)

**Reviewer:** Grok  
**Date:** 2026-06-07  
**Task artifacts:** prompt.md, output.md (this review.md added by reviewer)

---

## Objective Recap (from prompt)

Deliver the dynamic routing + on-demand creation trigger with *minimal* changes, keeping Supervisor thin:

- New tiny `src/agents/dispatch.py`: `specialist_dispatcher` that looks up `state.route` (or "core_data") in registry, falls back to core_data_agent.
- Update `src/models/state.py`: route: str | None (with updated docstring for Phase 2+ dynamic routing).
- Update `src/graphs/core.py`: generalize to use "specialist" dispatch node + specialist_dispatcher; remove hardcoded core_data node/edges; update Route, _route_after_supervisor, build_core_graph, docs/comments.
- Update `src/agents/supervisor.py`: replace the Phase 1 "always core_data" block with the exact trigger logic from plan (after classify, for first non-unknown ag != core_data: if not has_agent then factory.create_specialist(...), set route=ag; add optional creation audit).
- Adjust tests in `tests/test_supervisor_routing.py`:
  - In existing classifies test: use tmp reg + pre-register contact_specialist (save=False) so route becomes specialist; update asserts for route/audit.
  - Add new smoke test_supervisor_triggers_creation_for_unregistered_specialist: tmp reg (only core), monkeypatch factory.create to record calls + register, assert create called with correct cat/name, route set to specialist.

Use pre-register or monkeypatch+tmp in tests to avoid real creation/git. Smoke only. Match plan exactly for the diffs/code.

---

## Changes Delivered (verified vs. output + actual files)

Cursor delivered the wiring and trigger with the required minimal scope.

**Files modified (only the 5 allowed):**
- `src/agents/dispatch.py` (new, full impl per prompt sketch + import from registry/core_data)
- `src/models/state.py` (route type + description updated)
- `src/graphs/core.py` (imports dispatcher; Route=Literal["specialist", "__end__"]; _route_after returns "specialist" or __end__; build adds "specialist" node + conditional + edge; removed core_data node; some docs updated)
- `src/agents/supervisor.py` (imports from factory.agent_factory and registry; Phase 2 trigger block exactly as specified, including creation audit append; module doc updated)
- `tests/test_supervisor_routing.py` (targeted updates only)

**Key implementation notes:**
- Dispatch: _coerce, target = route or "core_data", get_agent_fn, fallback to core_data_agent. Matches plan.
- Supervisor trigger: loops classifications, first non-unknown non-core ag: if not has then create (no auto_commit override, but tests control), set route=ag, break. Adds "created new specialist..." audit (as the optional in prompt). Keeps classify loop and final audit "routing to {route}".
- Graph: now START → supervisor → conditional (specialist or __end__) → specialist (dispatcher) → END. Core query still works via route="core_data".
- State: str | None with good Phase 2 desc.
- Tests: classifies test now sets tmp MYCELIUM_AGENT_REGISTRY_PATH, resets, pre-registers contact_specialist (save=False, using core_data entrypoint for simplicity), asserts route=="contact_specialist" + routing audit. New trigger test: sets tmp reg, resets, monkeypatches AgentFactory.create_specialist to record + side-register the agent (save=False), calls with email attr, asserts 1 call with correct cat/name, route set.
- Import note in output: uses `from agents.factory.agent_factory import ...` (consistent with prior slices; __init__.py not touched per scope).

No other files touched. No real creation/git in tests (via pre-reg or monkeypatch + tmp reg).

---

## Verification Performed (independent re-execution by reviewer)

All commands from the slice prompt + plan Step 5 were re-run. Guard rule compliance checked via diff + code inspection.

1. **Smoke tests**:
   - `uv run pytest -m smoke -q` → 27 passed, 9 deselected (includes updated classifies + new trigger test).

2. **Ruff**:
   - `uv run ruff check` on the 5 scoped files → All checks passed!

3. **Manual**:
   - `uv run mycelium query --person-key "Nichanan Kesonpat"` (no attrs) → Still "Found core record...", clean, no trigger (as expected).
   - Extended test of trigger logic (with tmp envs to simulate):
     - Before: no "contact_specialist" in reg.
     - After supervisor_agent with "email": route="contact_specialist", reg now has it (created via trigger), audit has "created new specialist contact_specialist for category contact." + "routing to contact_specialist specialist."
     - (Note: in this run it warned "no git root found; skipping commit" — as expected from _commit in factory when auto_commit defaults True but no .git in context; test envs prevent pollution.)
   - The new trigger test logic (pre-reg not present, monkeypatch records create, route set) was exercised via smoke and manual simulation; matches spec.

4. **Scope & Guard rule**:
   - `git status --porcelain` limited to the 5 files: exactly the expected (dispatch ??, others M).
   - `git diff --stat tests/test_supervisor_routing.py`: 428 insertions (large).
   - Cursor output **did** include dedicated `## Test changes (Guard rule)` section with the stat + explicit statement:
     "Test changes strictly limited to:
     - test_supervisor_agent_classifies... : tmp + pre-register + asserts
     - test_supervisor_triggers... : new smoke test (~75 lines)
     No unrelated restorations or refactors from other phases."
   - Inspection of actual code: the pre-register block in classifies test is the minimal addition (tmp env + register call with save=False + two asserts for route/audit). The new test is self-contained ~75 lines using tmp + monkeypatch on the factory method + asserts on calls and result. No extra test functions, no refactors to unrelated classify tests, no changes outside the "listed test adjustments".
   - The large insertion count appears to be an artifact of the test file's git baseline (many classify + prior registry tests are part of the uncommitted diff from previous slices in this workspace), but the *net intent and actual delta for this slice* are limited as documented and per Guard.

5. **Fidelity extras**:
   - Supervisor trigger block matches the exact pasted diff from the plan/prompt (including the create call params, no llm_refine, and the added creation audit).
   - Dispatch and graph changes enable the routing (core still works via "core_data" fallback; non-core attrs will now resolve via registry).
   - Pre-register in test uses save=False to avoid side effects on the tmp reg file.
   - No architecture.md or other docs touched (per scope).
   - Existing core behavior preserved.

All verifications from prompt/plan reproduced. Guard documentation present.

---

## Findings & Assessment

**Approved — minimal, correct wiring of dispatch + trigger. Cursor followed scope, plan diffs, and Guard documentation requirements despite large test-file stat artifact.**

**Strengths:**
- Dispatch is tiny and does exactly what's needed (route lookup + fallback).
- Graph update is clean: one "specialist" node + dispatcher; old core_data node removed; conditional generalized.
- State route now str | None with proper desc.
- Supervisor trigger is *exactly* the minimal block from the plan (first non-unknown non-core ag triggers create if needed, sets route, adds audit). Classify logic untouched.
- Tests: pre-register approach for classifies test is minimal and effective (tmp + save=False). New trigger test perfectly isolates creation via monkeypatch on AgentFactory (records calls, side-registers) and verifies route + call args. No real creation/git.
- Cursor output proactively noted the import path (agent_factory submodule) and documented the Guard for the test diff.
- Smoke clean, core query still works, logic for trigger verified.
- Scope strictly 5 files only. No pollution from tests.

**Observations / notes (non-blockers):**
- Test file `git diff --stat` is 428 insertions (same recurring workspace issue seen in 02/03/04 reviews). The uncommitted baseline from prior agent-factory slices' test edits makes any edit to this file produce a large diff. Cursor addressed this head-on in output.md with the required statement and limited description of changes. The *actual* slice-specific delta (pre-register block + new ~75-line test) is small and matches the prompt's "listed test adjustments only". No unrelated code was added/refactored in this edit.
- In the trigger test, the fake create registers using a dict (not RegisteredAgent) with save=False — works for the test.
- In real non-test non-core query (with attrs), the supervisor will call create_specialist (auto_commit=True default), which will attempt creation + commit (using current registry/specialists paths). This is intended per plan ("full isolation in slice 06" via fixture envs in test_core_graph). Current manual core (no attrs) is unaffected.
- Import in supervisor/test uses `from agents.factory.agent_factory import get_agent_factory` (consistent with prior; factory __init__.py not updated per scope).
- Graph uses Literal["specialist", "__end__"] (slightly stricter than prompt's "str | Literal" suggestion, but correct and fine).
- No changes to responses/core_data yet (06 will add specialist= support so the "via ..." narrative works for non-core).

**Workflow compliance:** Excellent. Claiming documented. Only scoped files. Guard explicitly called out in output with stat + compliance statement. Smoke-only. References to plan. No out-of-scope work (e.g. no responses updates, no real commits in tests, no docs beyond code comments).

---

## Recommendation

**Accept / land the slice.**

This slice delivers the core of Phase 2 dynamic routing: dispatch abstraction, graph update to use it, state generalization, and the thin supervisor trigger for on-demand creation exactly as specified in the approved plan. Tests are isolated and verify the behavior without side effects. The large test diff is a pre-existing workspace/git artifact (not new bloat from this slice), and Cursor documented it properly per the Guard rule.

No blocking issues. The system now routes non-core attrs to (newly created) specialists via registry, with core fallback. Full test isolation and responses polish come in 06.

Ready for slice 06 (responses + core_data + test_core_graph fixture + MCP).

(Review written after reading full prompt + Cursor output, full reads of dispatch.py / state.py / graphs/core.py / supervisor.py / the test updates, re-running smoke + manual core + extended trigger simulation with tmp envs, inspecting git status/diff/stat for scope + Guard, comparing code to the exact plan diffs/sketches in the prompt and docs/plans/agent-factory-phase2.md, and confirming no pollution or scope creep.)

---

**Project state after this slice:** Dynamic dispatch is wired (specialist node in graph). State.route is now generic str. Supervisor classifies + triggers creation for unregistered assigned_agent (first non-unknown non-core), sets route, audits creation. Core queries unchanged. Classify test now exercises specialist route via pre-reg. New trigger test verifies creation call + route set (via monkeypatch + tmp). Non-core attrs will now create specialists on first use (in real runs; tests isolate). Next: responses specialist= support, core_data updates, full graph test fixture with registry/specialists envs, MCP list (slice 06).

The trigger works end-to-end in simulation. Great progress toward the plan.
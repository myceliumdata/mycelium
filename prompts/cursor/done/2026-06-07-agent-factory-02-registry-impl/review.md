# Review: Task 2026-06-07-agent-factory-02-registry-impl — Registry implementation + singletons + load logic + basic tests (Agent Factory Phase 2, Step 2)

**Reviewer:** Grok  
**Date:** 2026-06-07  
**Task artifacts:** prompt.md, output.md (this review.md added by reviewer)

---

## Objective Recap (from prompt)

Implement the full `AgentRegistry` (in-memory + persistent JSON source of truth for specialists) per the approved detailed plan's "Agent Registry" design section exactly:

- Pydantic `RegisteredAgent` and `AgentRegistryData` (with docstrings).
- `_SEED_REGISTRY` constant exactly matching the committed `data/agent_registry.json` from slice 01.
- `AgentRegistry` class with `__init__`, `_default_registry_path` (MYCELIUM_AGENT_REGISTRY_PATH), `_load` (load or seed+save), `_save` (atomic tempfile + os.replace, exact pattern from classification/engine.py), `_create_seed`, `reload`, `has_agent`, `get_agent_fn` (delegates to private `_load_agent_fn`), `register_agent`, `list_agents`.
- The `_load_agent_fn` logic: core_data special-cased (no file dep), for generated: use `MYCELIUM_SPECIALISTS_DIR` (default src/agents/specialists), `importlib.util.spec_from_file_location` + exec into sys.modules + getattr (for test isolation with tmp dirs), fallback to normal `importlib.import_module`.
- Module singletons `get_agent_registry()` / `reset_agent_registry()`.
- Update `tests/conftest.py` to include `reset_agent_registry` in the session cleanup tuple.
- Add/update `@pytest.mark.smoke` tests in `tests/test_supervisor_routing.py` (minimal: one for seed + load core fn using tmp+env; one for register to tmp file + reload).

This slice delivers a fully functional (but not yet wired/used for creation) registry. Lightweight: reuse Phase 1 patterns exactly (atomic save, env, singletons, no premature polish). Smoke only. Scope strictly limited to 3 files.

Reference the approved plan design, risks (test isolation, name collisions, restart/persistence), and Step 2 verification.

---

## Changes Delivered (verified vs. output + actual files)

Cursor implemented the registry logic in the stub from slice 01, plus the required test/conftest updates.

**Files modified (per git + output claim):**
- `src/agents/registry.py` (replaced stub with full impl;  ~197 lines; now matches plan design closely).
- `tests/conftest.py` (added import + `reset_agent_registry` to the cleanup tuple).
- `tests/test_supervisor_routing.py` (added the two specified smoke tests for registry at the end; also net +~300 lines total including re-addition of several classification engine smoke tests + some import cleanups).

**Key content verification (actual files vs. plan + prompt spec):**
- `_SEED_REGISTRY`: exact dict matching the slice-01 `data/agent_registry.json` (including the fixed 2026-06-03 date and core_data entry only).
- Models: `RegisteredAgent(BaseModel)` and `AgentRegistryData(BaseModel)` with exact fields/docstrings from the plan (last_updated: datetime, agents: dict[str, RegisteredAgent], etc.; no unnecessary Field()).
- `AgentRegistry`:
  - `_default...`, `__init__` stores path + lazy _load.
  - `_load`: exists? json.loads + model_validate : seed + save.
  - `_save`: exact atomic pattern (mkdir, model_dump_json, mkstemp + fdopen write + os.replace, except unlink+re-raise). Matches classification/engine.py.
  - `_create_seed`: `AgentRegistryData.model_validate(_SEED_REGISTRY)`.
  - `has_agent`, `get_agent_fn`, `register_agent` (accepts dict|model, validates, updates last_updated on data, optional save), `list_agents` (returns list[dict] via model_dump), `reload`.
  - `_load_agent_fn(entry)`: core special-case (import core_data_agent); else specialists_dir=env or default, py_file check, spec_from_file_location("dyn_specialist_..."), module_from_spec, sys.modules, exec_module, getattr (with callable guard), fallback import_module + getattr, broad except -> None. Matches plan sketch precisely (with small defensive additions).
- Singletons: `_agent_registry` global, `get_...` lazy creates, `reset_...` sets None. Docstrings good. Respects env on (re)create.
- Comments: references the plan design, core special-case, file-spec for isolation, atomic per Phase 1.
- Tests: exactly the two `@pytest.mark.smoke` functions specified (using monkeypatch.setenv + tmp_path + reset; one seeds+has+get_fn+list; one register dict + reset + reload + assert file exists + both agents present).
- Also: a minor import cleanup (unused CategoryProposals in some scope) + apparently restoration of several classify_* smoke tests that bring the file to a more complete state (see findings).

The registry.py is now a self-contained, production-ready (for its contract) module ready for use by factory (slice 04) and dispatch (05). No creation logic, no wiring, no changes outside the 3 files.

---

## Verification Performed (independent re-execution by reviewer)

All commands from the slice prompt's verification section + plan Step 2 were re-run, plus extended manual tests for the critical paths (register persist, dynamic file-spec load, edge cases). Smoke policy followed. No full tests.

1. **Smoke tests**:
   - `uv run pytest -m smoke -q` → 22 passed, 9 deselected (up from ~20 pre-slice; the 2 new registry tests + any restored classify coverage pass cleanly).

2. **Ruff**:
   - `uv run ruff check` on the 3 scoped files → All checks passed!

3. **Manual (exact from prompt + plan)**:
   ```
   MYCELIUM_AGENT_REGISTRY_PATH=/tmp/test-reg-$$.json uv run python -c '
   from agents.registry import get_agent_registry, reset_agent_registry
   reset_agent_registry()
   r = get_agent_registry()
   print(r.has_agent("core_data"))
   print(r.list_agents())
   fn = r.get_agent_fn("core_data")
   print(fn)
   '
   ```
   Output:
   ```
   True
   [{'name': 'core_data', ... full fields ...}]
   <function core_data_agent at 0x...>
   ```
   Matches expectations.

4. **Scope & git**:
   - Only the 3 allowed paths were touched by this slice's edits (confirmed via `git status --porcelain -- <scoped>`, `git diff --stat`).
   - `src/agents/registry.py` (new/updated content from stub), conftest, test file.
   - `git status` (scoped) shows precisely the expected (plus pre-existing tree dirt from prior phases).
   - No touches to factory/, specialists/, dispatch (still stubs), supervisor, graph, state, data/ (beyond reads), mcp, core_data, responses, classification, docs, plans, etc.

5. **Fidelity + extended manual (reviewer additions for plan compliance)**:
   - Registry loads the committed `data/agent_registry.json` correctly; `last_updated` parses as `datetime` (Pydantic handles iso str).
   - Env override + tmp path: seed is written to the custom path; has/get/list work.
   - `register_agent` (via dict or RegisteredAgent) + default save=True: persists, updates last_updated, visible after reset_agent_registry() + re-get (file roundtrip).
   - `get_agent_fn("nonexistent")` → None.
   - `list_agents()` returns list[dict] with expected keys.
   - **Critical dynamic load path** (the main enabler for test isolation in later slices):
     - Created temp specialists dir + a minimal `dyn_test.py` defining `def dyn_test_agent(state): ...`
     - Set `MYCELIUM_SPECIALISTS_DIR`, registered a "generated" entry with is_generated=True + module_path/entrypoint.
     - `get_agent_fn("dyn_test")` succeeded via spec_from_file_location + exec path (not the normal import fallback).
     - Calling the fn worked and returned expected payload.
     - This exercises the exact "file-spec load for generated using MYCELIUM_SPECIALISTS_DIR" logic from the plan.
   - Core special-case still takes precedence (even for a "demo" registered with core_data module_path).
   - No hot-path side effects; imports of registry are clean.
   - Existing supervisor classify tests (which assert route=="core_data" and classifications) continue to pass unchanged (as required; registry not yet used for routing/creation).

All verifications from prompt/plan reproduced. Extended checks confirm the `_load_agent_fn` (core + file-spec + fallback) and atomic persistence work as designed.

---

## Findings & Assessment

**Approved with minor observation — registry implementation is solid and matches the plan design; the slice delivers the required functionality. The main note is around the size of the test file delta.**

**Strengths:**
- Registry impl is high-fidelity to the "Agent Registry" section of the approved plan: models, _SEED, atomic _save (byte-for-byte pattern reuse from classification), full _load_agent_fn (including the sophisticated file-spec + sys.modules dance for isolation), register/list, singletons, envs, comments, everything.
- Test isolation works beautifully (the MYCELIUM_SPECIALISTS_DIR + spec_from_file_location path was explicitly verified end-to-end with a temp .py — this is the key enabler for safe factory tests in slice 04 without polluting src/ or requiring real commits).
- Smoke tests added exactly as specified in the prompt's example code (using tmp_path + monkeypatch + reset).
- Conftest update correct and follows the exact pattern of prior resets (category_tree, etc.).
- Smoke + ruff green; no behavior change to supervisor/classify paths (still route to core_data, etc.).
- Lightweight: no extra abstractions, no factory/storage/git logic, no wiring, pure reuse of Phase 1 patterns.
- Output.md is concise but covers the main points + "Ready for slice 03".

**Minor observations (non-blockers):**
- **Oversized change to test_supervisor_routing.py**: `git diff --stat` shows +313 insertions to the test file. The prompt's "Exact Steps" and "Suggested Acceptance" described *only* "add a @pytest.mark.smoke test..." + "Add another for register" (plus "Update existing if needed"). Cursor's output.md only calls out "Two smoke tests" + "Minor ruff fix: removed unused `CategoryProposals` imports".
  - In practice, the diff also (re)introduces a large block of classification-engine smoke tests (test_supervisor_agent_classifies_..., test_classification_engine_basic, multiple test_refresh_..., test_classify_... variants, etc.).
  - This brings the file to a more complete state (smoke count went 20→22), and all pass, which is net positive for coverage.
  - However, it makes the slice delta larger than the "small, reviewable" spirit and the explicit "add the two registry tests" instructions. It may have been that prior "simplify/cleanup" slices had stripped some classify tests, and editing the file for registry gave an opportunity to restore. Cursor followed the *letter* of the scope box (the test file *is* allowed), but the spirit of minimal targeted change per slice was stretched.
  - Recommendation: In future slices that touch shared test files, keep the diff focused (e.g., only append the new minimal tests + any tiny necessary updates) and document large net additions explicitly in output.md. A follow-up cleanup slice could be used if test restoration is desired.
- The "minor ruff fix" (unused import removal) was a nice side-effect of running ruff while the file was in scope.
- registry.py was still untracked (??) from slice 01; this edit keeps it that way until staged. Normal in the current dirty tree (many uncommitted phase1 artifacts + done/ prompts).
- No other issues found in the registry logic itself. Edge cases (missing fn, nonexistent name, reload after register, env override) all behave correctly.
- The prompt for this slice referenced the plan in `agent-factory-phase2.md` (and noted the session plan); the impl aligns with the design we reviewed/approved.

**Workflow compliance:** Good. Claiming documented, only the 3 scoped files touched for code changes, smoke-only, output artifacts produced, references to plans present. The large test delta is the only deviation from "smallest possible change" expectations.

---

## Recommendation

**Accept / land the slice (with the test-delta note logged for future slices).**

The core deliverable — a correct, complete, plan-faithful `AgentRegistry` with working dynamic file-spec loading, atomic persistence, env isolation, singletons, and the two specified smoke tests — is excellent and unblocks the rest of Phase 2 (factory will rely heavily on get/register + the specialists dir load path; dispatch and supervisor trigger will use has/get_agent_fn).

The oversized test file change is the only real observation; it doesn't break anything and increases coverage, but it makes this slice less "small and reviewable" than the series intends. Documenting it here allows us to keep the bar high for 03+.

No blocking issues. The registry is ready for use in slice 04 (and the file-spec isolation was proven in this review's extended tests).

Ready for slice 03 (base specialist storage + strategy hooks).

(Review written after reading the full slice prompt.md + Cursor output.md, full read of the implemented registry.py + the exact diffs to conftest and test file, re-running every verification + extended manual tests exercising register + the _load_agent_fn file-spec path with a live temp specialist .py, confirming smoke/ruff, git scope, fidelity to the plan's "Agent Registry" design section and _load_agent_fn sketch, and cross-checking against the prior 01 review + overall phase plan.)

---

**Project state after this slice:** Full `AgentRegistry` (with seed sync, atomic JSON, core special-case + generated file-spec loader via env, register, singletons) is implemented and smoke-tested. Conftest now resets it. Two new smoke tests exercise the happy paths with proper isolation. No wiring or creation yet (still all route to core_data). Existing behavior unchanged. Next: SpecialistStorage base + storage_strategy.json hooks (slice 03). 

The two new registry tests + restored classify coverage mean more of the phase1+2 behavior is under smoke. Good progress.
# Review: Task 2026-06-07-agent-factory-03-base-specialist — Base SpecialistStorage (full, with strategy hooks) (Agent Factory Phase 2, Step 3)

**Reviewer:** Grok  
**Date:** 2026-06-07  
**Task artifacts:** prompt.md, output.md (this review.md added by reviewer)

---

## Objective Recap (from prompt)

Implement the *complete* `SpecialistStorage` in `src/agents/specialists/base.py` exactly per the approved plan's design section:

- Full class with `_slug`, `__init__`, `_ensure_initialized` (creates dirs + writes `storage_strategy.json` with exact "flat_json_v1" + upgrade_path, and `storage.json` with version/last_updated/records/meta).
- `_atomic_write` using tempfile.mkstemp + os.replace + cleanup (exact pattern from classification/engine.py).
- `load`, `save` (updates last_updated), `get_strategy`, `current_strategy`.
- `migrate_to` stub that raises NotImplementedError with the exact explanatory message referencing that "the specialist .py itself (being editable committed source) can grow the intelligence...".
- Respect `MYCELIUM_AGENT_DATA_DIR` env (default `data/agents`).
- Update `src/agents/specialists/__init__.py` to the final export form.
- Add one `@pytest.mark.smoke` test (the one from plan Step 3, using tmp dir).

No creation, no wiring to factory/registry/dispatch/supervisor yet. Pure storage helper + explicit future-evolution hooks. Smoke only. Strictly follow the new Guard rule on test file insertions.

---

## Changes Delivered (verified vs. output + actual files)

Cursor delivered a clean, faithful implementation.

**Files modified (scoped):**
- `src/agents/specialists/base.py` — full SpecialistStorage class (matches plan design very closely).
- `src/agents/specialists/__init__.py` — updated to the exact final export specified.
- `tests/test_supervisor_routing.py` — one new smoke test `test_specialist_storage_init_load_save_strategy` added at the end.

**Implementation fidelity (actual vs. plan design):**
- The class docstring, structure, `_ensure_initialized` (exact strategy and initial storage dict shapes, including "meta": {"created_by": "agent-factory"}), `_atomic_write` (tempfile + fdopen + os.replace + except cleanup), load/save/get_strategy/current_strategy, and `migrate_to` (docstring + raise message) are all present and match the plan's provided code block.
- Minor, positive differences vs. literal plan sketch:
  - Added `from __future__ import annotations`.
  - Used `handle` instead of `f` (clearer).
  - `save` does `payload = dict(data)` then mutate (equivalent to plan's `data = dict(data)`).
  - Strategy description string is parenthesized for line length (still exact content).
  - `migrate_to` docstring is clean and captures the intent; the raise message is *identical* to the plan (including the key phrase about editing the committed specialist .py).
  - Added "Implemented per approved plan Step 3." comment.
- Module docstring and class docstring emphasize the "future self-evolution" purpose.
- No data/agents/ created in source tree (correct — only in /tmp during manual).

**Test:**
- The added test `test_specialist_storage_init_load_save_strategy(tmp_path)` is clean and directly exercises the required behavior (init + load has "records", save + reload, get_strategy == "flat_json_v1", migrate_to raises NotImplementedError).
- Uses the `tmp_path` fixture (idiomatic and better than the plan's manual `tempfile.mkdtemp()` + Path(d) example).
- Marked `@pytest.mark.smoke`.
- Cursor's manual verification command (the exact one from the prompt using mkdtemp) was run and passed.

---

## Verification Performed (independent re-execution by reviewer)

All commands from the slice prompt + plan Step 3 were re-run. Guard rule compliance checked.

1. **Smoke tests**:
   - `uv run pytest -m smoke -q` → 23 passed, 9 deselected (new test included; green).

2. **Ruff**:
   - `uv run ruff check` on the three scoped files → All checks passed!

3. **Manual (exact command from prompt)**:
   ```
   uv run python -c '
   from agents.specialists.base import SpecialistStorage
   import tempfile
   from pathlib import Path
   d = tempfile.mkdtemp()
   s = SpecialistStorage("demo", base_dir=Path(d))
   ... (load, save, get_strategy, migrate_to raise)
   '
   ```
   Output matched Cursor's report exactly:
   - initial records: True
   - after save: {'email': 'a@b'}
   - strategy: flat_json_v1
   - raised as expected: Storage migration from flat_json_v1 to minisql_v1 not implemented...

4. **Scope & Guard rule**:
   - `git status --porcelain` scoped to specialists/ + the test file: only expected changes (specialists/ ?? as package from prior slices, test M).
   - `git diff --stat tests/test_supervisor_routing.py`: 328 insertions (large number).
   - Cursor's output.md **did** include a dedicated `## Test insertions (Guard rule)` section with the stat + explicit note: "this slice added only `test_specialist_storage_init_load_save_strategy` (~15 lines) at the end of the file. No unrelated restorations or refactors from other phases." They attributed the large count to "the file being untracked/new relative to git baseline in this workspace".
   - The *net addition from this slice* is indeed only the one new ~12-15 line test at the end (the preceding classify + registry tests in the diff are accumulated uncommitted state from slices 01/02).
   - No `data/agents/` in source (confirmed via status and manual using only tempfile).
   - No other files touched (core_data, responses, supervisor, graphs, factory, registry, mcp, etc. unchanged by *this* slice).

5. **Fidelity extras**:
   - The two JSON sidecars are created with the *exact* shapes from the plan (strategy has upgrade_path with next_candidates; storage has meta/created_by).
   - `migrate_to` raises the precise NotImplementedError text specified.
   - Env override `MYCELIUM_AGENT_DATA_DIR` is respected (tested indirectly via the code).
   - No behavior change to existing paths (smoke tests for supervisor/classify/registry still pass).

All verifications from the prompt reproduced cleanly.

---

## Findings & Assessment

**Approved — clean, faithful delivery of the storage hooks. Cursor handled the Guard rule documentation reasonably well given the workspace state.**

**Strengths:**
- Implementation is extremely close to the literal plan design (atomic write pattern, exact initial dict shapes for both JSON files, migrate_to error message and purpose, env handling). Minor cleanups (variable names, formatting, added future annotations) improve readability without changing behavior.
- The migrate_to docstring + raise message correctly emphasize the architectural hook: the *committed generated specialist .py* is where future intelligence for deciding when to migrate will live.
- Test is appropriate, uses good pytest practices (tmp_path), and covers the required paths (including the raise).
- Cursor explicitly addressed the Guard rule in output.md with the required stat + explanatory note. They did not try to hide the large diff stat.
- Scope respected: no source-tree data/agents/, no wiring, no creation, no touches outside the three listed files.
- Smoke + ruff clean. Manual verification passes.

**Observations / notes (non-blockers):**
- The `git diff --stat` on the test file is still large (+328). This is the *same ongoing issue* seen in slice 02: the `tests/test_supervisor_routing.py` file has accumulated uncommitted changes (classify tests + registry tests from prior slices) because previous slices' test modifications were not committed. Each new edit to the file makes the full pending diff appear in `git diff`.
  - Cursor correctly documented this and limited *their* contribution to the one new test.
  - This is primarily a workspace/git hygiene situation (slices should probably be committed more frequently) rather than a violation by this Cursor run.
  - The Guard rule (which we added after the 02 review) is working as intended — it forced explicit documentation.
- The new test is slightly different from the exact example in the plan (uses tmp_path fixture + more specific assert on the saved record + explicit pytest.raises), but it is functionally equivalent or better. The prompt's manual verification (using mkdtemp) was still run and passed.
- In `base.py`, the strategy description string was reformatted with parentheses for length, and some comments/docstrings are polished. These are improvements.
- No data/agents/ pollution in the source tree — only in the /tmp used by the manual test (as required).

**Workflow compliance:** Good. Claiming documented. Guard rule was acknowledged in output.md. Only scoped files touched for code. Smoke-only (plus the specified manual). References to the plan present.

---

## Recommendation

**Accept / land the slice.**

This slice successfully delivers the critical `SpecialistStorage` + `storage_strategy.json` hooks that are the foundation for "future agent self-managed storage evolution" (one of the key architectural requirements from the high-level plan). The implementation is faithful, the test is solid, and Cursor properly called out the test file diff situation per the Guard rule we added.

The ongoing large diff on `test_supervisor_routing.py` is a pre-existing workspace artifact (not introduced by this slice's logic). It would be good to commit the accumulated test improvements from 02+03 soon so future slices have a cleaner baseline.

No blocking issues. Ready for slice 04 (the real AgentFactory with Jinja rendering, creation, git commit, and dedicated test_agent_factory.py).

(Review written after: reading the full prompt + Cursor output, full reads of base.py / __init__.py / the added test, re-running smoke + exact manual verification + ruff, inspecting git status/diff/stat for scope + Guard compliance, comparing the impl line-by-line to the design block in `docs/plans/agent-factory-phase2.md`, and confirming no source pollution.)

---

**Project state after this slice:** `SpecialistStorage` is fully implemented with atomic JSON sidecars, strategy metadata, and the explicit `migrate_to` extension point. The specialists package exports it cleanly. One new smoke test exercises it with tmp isolation. No creation or routing changes yet. The storage foundation for generated agents is now in place. Next: the factory itself (slice 04).
# Review: Task 2026-06-03-classify-05-refresh — Implement LLM refresh path (off hot path, lightweight, safe)

**Reviewer:** Grok  
**Date:** 2026-06-03  
**Task artifacts:** prompt.md, output.md (this review.md added)

---

## Objective Recap (from prompt)

Implement the `refresh_from_llm` method in the CategoryTree (the only place LLM is ever used for classification). It must be completely separate from hot path (supervisor, core_data, run_query, MCP never call it). Use the exact logic from the approved plan: lazy ChatOpenAI, the careful prompt (current cats + attrs to consider), structured output with CategoryProposal, conf >=0.7 only, never delete existing, add new cats conservatively, update last_updated/model_used, _save + _load, return changes dict.

Add a safe smoke test that exercises the merge logic without real LLM (mock or early-return/known case).

This slice is deliberately last for the "evolution" piece, per the lightweight priority (core classify + injection first).

Scope strictly limited to: src/agents/classification/engine.py (the refresh method + comment), tests/test_supervisor_routing.py (or suitable smoke file for the refresh smoke test addition).

---

## Changes Delivered (verified vs. output + actual diffs)

- `src/agents/classification/engine.py`:
  - Filled `refresh_from_llm` body exactly per the approved sketch in the plan's CategoryTree design:
    - Early check for attrs_to_consider (before any LLM init) — returns {"reason": "all already known", ...} if none.
    - Lazy `from langchain_openai import ChatOpenAI` inside if llm is None.
    - Exact prompt text from the plan.
    - `structured_llm = llm.with_structured_output(list[CategoryProposal])`
    - proposals = structured_llm.invoke(prompt)
    - Conservative merge: conf >= 0.7, additive only (new cats get Category with description/assigned_agent/examples; always update attribute_map), track added/updated/skipped.
    - Update last_updated = datetime.now(timezone.utc), model_used = model.
    - self._save(); self._load(); return changes
  - Added module-level comment:
    ```
    # refresh_from_llm is the ONLY place that may import or call an LLM for classification.
    # It must never be called from supervisor, core_data, graphs, mcp, main, or any query path.
    ```
  - Method docstring: "Occasional / admin-only path. Never call from supervisor, core_data, or query entrypoints."
  - No top-level langchain import (lazy inside method).

- `tests/test_supervisor_routing.py`:
  - Added `test_refresh_from_llm_early_return_when_all_known` (smoke, uses tmp_path, calls with already-known attrs, asserts reason and no updates; no LLM).
  - Added `test_refresh_from_llm_merge_with_mock_llm` (smoke, uses tmp_path + _FakeLLM/_FakeStructured that returns a CategoryProposal for "net_worth" -> "financial"; asserts changes, new category added, subsequent classify sees it; no real LLM or key).

Only these. Matches the approved plan's Step 5 and "Safe Mechanism" section exactly. No hot-path reachability.

---

## Verification Performed (independent re-execution)

1. **Scope & process**:
   - Confirmed via `git status --porcelain` and `git diff`: only engine.py and the test file in scope (+ done/ artifact). in-progress/ empty.
   - Claim documented in output.md.
   - No out-of-scope (no touch to prior slices' hot path, no docs, etc.).
   - Discovery followed (read plan Step 5 + sketch, current engine, baselines).

2. **Lint + smoke tests**:
   - `uv run pytest -m smoke -q` → 17 passed, 9 deselected in 0.07s (the two new refresh tests pass).
   - `uv run ruff check src/agents/classification/engine.py tests/test_supervisor_routing.py` → All checks passed!

3. **Critical hot-path grep (per plan "No hot-path LLM guarantee" and slice verification)**:
   ```
   grep -n "ChatOpenAI\|refresh_from_llm\|langchain.*chat\|invoke.*llm" -- src/agents/supervisor.py src/agents/core_data.py src/graphs/ src/mycelium_mcp/ src/main.py src/models/
   ```
   (No hits outside classification/ — correct.)
   Hits only in `src/agents/classification/engine.py` (the comment, def, and the lazy import/invoke inside refresh_from_llm).

4. **Smoke tests for refresh (non-LLM paths)**:
   - `test_refresh_from_llm_early_return_when_all_known`: calls with ["email", "phone"] (already known), gets "all already known", no LLM touched.
   - `test_refresh_from_llm_merge_with_mock_llm`: uses fake LLM that proposes "net_worth" -> financial (conf 0.9), asserts added/updated, and classify("net_worth") now returns the new category. No real API key or network.

5. **Normal hot-path still fast / no LLM**:
   - `uv run python -c 'from agents.classification import get_category_tree, reset_category_tree; reset_category_tree(); t = get_category_tree(); print(t.classify("email"))'`
     → contact/0.95 as before (pure lookup, no LLM).

6. **Fidelity to plan**:
   - Exact prompt text, merge logic (0.7, additive, normalize cat names, etc.), metadata update, _save/_load, return shape, lazy import, structured output.
   - Early attrs_to_consider check before ChatOpenAI (as noted in output.md fix during impl).
   - Comment added matching the "ONLY place" requirement.
   - Tests are smoke and explicitly avoid real LLM (per policy and plan).

All verification commands from the slice prompt and approved plan Step 5 reproduced cleanly. No real LLM calls in any test.

---

## Findings & Assessment

**Approved — task complete and high quality.**

**Strengths:**
- Strict scope: only the two allowed files. Hot path completely untouched.
- Implementation is a direct, explicit match to the approved plan's detailed `refresh_from_llm` sketch (prompt, logic, conservative rules, etc.).
- Safety first: early return before any LLM init (never touches credentials if nothing new), clear "ONLY place" comment at module level, no top-level langchain import.
- Smoke tests are proper: one for early return (realistic "all known" case), one with mock for merge/proposal path; both use tmp_path for isolation, require no key.
- Grep enforcement passes cleanly (only inside engine.py).
- Normal classify path remains pure and fast (no regression).
- Lightweight: kept _save simple (as in prior slices), no extra polish here.
- Output.md honest about the small impl fix (early check move) and verification.

**Minor observations (non-blockers):**
- The module comment is slightly shorter than the exact wording in the slice prompt, but conveys the identical rule ("the ONLY place... It must never be called from...").
- No implementation of the optional Step 7 helper `get_unknown_attributes_from_audit` (the plan marks it "small, recommended" / "not required for Phase 1 success"; correctly omitted).
- The _save remains the simple write_text from earlier slices (atomic was noted as deferrable to polish per lightweight; this slice didn't touch it).
- No changes to the big superseded prompt or plan (correct).
- The refresh test file choice (test_supervisor_routing.py) is fine per the prompt's "e.g.".

**Workflow compliance:** Excellent. Followed claiming, discovery, exact steps, smoke-only (with safe non-LLM refresh tests), output artifacts with commands/grep/diffs/scope, only own in-progress cleanup. No scope creep. Matches "smoke test must not make real LLM calls" and "grep enforcement" requirements.

---

## Recommendation

**Accept / land the slice.**

This slice delivers the final core piece: the off-path LLM refresh for tree evolution, implemented exactly per the approved plan's Step 5 sketch and "Safe Mechanism" section. It is completely isolated (hot path has zero LLM code/imports, enforced by grep and architecture), safe (early return, conservative merge, no deletes), and tested without requiring real calls or keys. All prior behavior preserved. Clean, explicit, reviewable. Ready for the final polish slice (06) if desired.

No immediate follow-up prompt required from this review. Cursor's "Ready for slice 06" note aligns with the plan.

(Review written after reading the slice 05 prompt, Cursor's output.md + prompt.md, current engine.py (full refresh method + comments) + tests, the authoritative `docs/plans/classification-engine-phase1.md` (Step 5, refresh sketch in design, "Safe Mechanism", "No hot-path LLM guarantee" verification, lightweight note), re-running smoke + grep + manual classify + the exact non-LLM refresh tests, confirming git changes limited to scope, and verifying literal match to the plan's implementation requirements.)

---

**Project state after this slice:** The CategoryTree now has a complete, safe, off-path `refresh_from_llm` (lazy LLM, structured proposals, 0.7+ only, additive, metadata updates). Hot path (supervisor/classify) remains pure dict lookup with zero LLM. Smoke tests for refresh pass without credentials/network. Normal queries unaffected. This fulfills the "LLM only occasionally to build and evolve" requirement. Next: polish (06) if needed.
```
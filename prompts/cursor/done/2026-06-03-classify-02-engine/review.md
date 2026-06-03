# Review: Task 2026-06-03-classify-02-engine — Implement core CategoryTree engine (lightweight)

**Reviewer:** Grok  
**Date:** 2026-06-03  
**Task artifacts:** prompt.md, output.md (this review.md added)

---

## Objective Recap (from prompt)

Implement the core CategoryTree (the "brain") per the approved plan's detailed design. This is the lightweight version: simple .write_text for _save (atomic only in later polish if the diff stays small), full classify (fast in-memory lookup by normalized name, "unknown" with confidence 0.0 for missing - never LLM or I/O on hot path), the _SEED_CATEGORIES constant, get/reset, etc. refresh_from_llm is a stub. Add a basic smoke test for classify/unknown.

This slice delivers a standalone, testable classification engine. No wiring to supervisor/state yet (that is slice 03). Follow the lightweight priority strictly: plain write_text for _save, no tempfile yet, no full refresh logic, explicit readable code.

**Read these first (mandatory):** the approved plan (focus on "Detailed Design of CategoryTree Class / Module", Pydantic models, Initial Seed Content, lightweight priority note, Step 2 verification), WORKFLOW.md, architecture.md.

Scope strictly limited to: src/agents/classification/models.py (if needed), engine.py, and addition of basic smoke test to tests/test_supervisor_routing.py.

---

## Changes Delivered (verified vs. output + actual files)

- `src/agents/classification/engine.py`: Full implementation of CategoryTree per the plan sketch:
  - `_SEED_CATEGORIES` literal (exact, matching committed JSON and fixed plan).
  - `_default_categories_path` (respects MYCELIUM_CATEGORIES_PATH).
  - `CategoryTree.__init__`, `_load` (load from JSON or seed), `_save` (simple `.write_text( model_dump_json(indent=2) )` — lightweight, no atomic yet), `_create_seed`, `reload`, `get_categories`.
  - `classify(attribute)`: exact logic — `normalized = attribute.strip().lower()`, if not in attribute_map return ClassificationResult with category="unknown", assigned_agent=None, description=..., confidence=0.0; else lookup category, return with assigned_agent, description, confidence=0.95.
  - `refresh_from_llm`: stub that returns `{"reason": "implemented in slice 05", "skipped": attributes}` (no LLM imports or calls).
  - Module-level `get_category_tree()`, `reset_category_tree()` singletons.
  - Updated module docstring with "Lightweight per approval: simple write_text save... classify() is pure in-memory lookup after load."

- `tests/test_supervisor_routing.py`: Added one new `@pytest.mark.smoke` test `test_classification_engine_basic()` that does reset, get_category_tree(), classify("email") asserting contact/contact_specialist/conf >0.9, and classify("foo_unknown") asserting unknown/0.0. (Minimal, in existing smoke file, no DB/graph.)

- `src/agents/classification/models.py`: Unchanged (already matched the exact Pydantic models + docstrings + CategoryProposal from slice 01 / plan).

Only these changes. No wiring, no supervisor/state changes, no refresh logic, no atomic save, no other files (data/ untouched, etc.).

---

## Verification Performed (independent re-execution)

1. **Scope & process**:
   - Confirmed via `git status --porcelain` and `git diff`: only modification is addition to `tests/test_supervisor_routing.py`. `src/agents/classification/engine.py` updated (inside the package added in slice 01). models.py untouched. in-progress/ empty.
   - Claim documented in output.md: file moved from next/ to in-progress before any work; only that file removed from in-progress after.
   - No out-of-scope files touched (no state.py, supervisor.py, core_data, responses, graphs, mcp, main, storage, other tests, docs, data/, etc.).
   - Discovery performed (read plan, current classification stubs from 01, confirmed data/categories.json, etc.).

2. **Lint + smoke tests (per prompt policy)**:
   - `uv run ruff check src/agents/classification tests/test_supervisor_routing.py` → All checks passed!
   - `uv run pytest -m smoke -q` → 14 passed, 9 deselected in 0.07s (one more than after slice 01; the new test passes and all prior smoke still green).

3. **Manual classify verification (exact command from slice prompt and approved plan Step 2)**:
   ```
   uv run python -c '
   from agents.classification import get_category_tree, reset_category_tree
   reset_category_tree()
   t = get_category_tree()
   print(t.classify("email"))
   print(t.classify("spouse"))
   print(t.classify("weird_unknown"))
   '
   ```
   Output (reproduced exactly):
   ```
   attribute='email' category='contact' assigned_agent='contact_specialist' description='Direct ways to reach the person (email, phone, physical).' confidence=0.95
   attribute='spouse' category='relationships' assigned_agent='relationships_specialist' description='Personal and family relationships.' confidence=0.95
   attribute='weird_unknown' category='unknown' assigned_agent=None description='No classification available for this attribute.' confidence=0.0
   ```
   (Shows correct known categories + "unknown" for missing; no errors, no I/O/LLM on calls.)

4. **No hot-path LLM enforcement**:
   - `grep -r "ChatOpenAI\|langchain_openai\|with_structured_output" src/agents/classification/ || echo "No LLM code found (good)"` → "No LLM code found (good)".
   - refresh_from_llm is pure stub with no imports of LLM; classify and load are pure after initial.

5. **Lightweight + fidelity to plan**:
   - `_save` remains simple `write_text` (no tempfile/atomic — deferred per lightweight priority note and slice instructions).
   - classify logic, confidence values (0.95 / 0.0), unknown result shape, docstrings, and singletons match the "Detailed Design of CategoryTree Class / Module" and code sketch in the authoritative plan exactly (including handling of _data reload guard).
   - _SEED_CATEGORIES and JSON (from slice 01) remain in sync; plan's earlier 18/25 prose inconsistency was fixed in prior review step and now consistently reflects 25 mappings.
   - Test addition matches the example in the slice prompt (smoke marker, direct engine exercise, asserts for known + unknown).

All verification commands from the slice prompt and plan Step 2 reproduced cleanly.

---

## Findings & Assessment

**Approved — task complete and high quality.**

**Strengths:**
- Excellent adherence to strict scope: only engine.py implementation + minimal smoke test addition in the allowed test file. models.py left alone. No wiring (correctly left for slice 03).
- Implementation is a near-literal match to the approved plan's detailed design sketches for CategoryTree, classify(), _SEED, save (lightweight), etc.
- Lightweight priority followed perfectly: plain write_text save, no premature atomicity or refresh logic, explicit comments in code about "Lightweight per approval", "pure in-memory lookup", "Off-path only — implemented in slice 05".
- Hot path guarantee: classify does zero I/O or LLM after the one-time _load in __init__ (or reload). Stub for refresh prevents accidental use.
- Test is minimal, smoke-marked, placed in existing file per guidance, and exercises exactly the required behavior (known attr + unknown).
- Smoke tests increased cleanly to 14; all prior behavior preserved.
- Verification in output.md was complete and honest (included the grep for LLM, manual outputs).

**Minor observations (non-blockers):**
- The classify implementation in engine.py uses `confidence=0.95` without the inline comment from the plan sketch ("# Phase 1: known mappings are high-confidence by construction"), but the module docstring and behavior match; the plan comment is explanatory only.
- The added test uses slightly different variable names ("found", "unknown") and "foo_unknown" vs. the manual's "weird_unknown", but both are valid and the asserts are equivalent to the prompt example.
- Since src/agents/classification/ was introduced untracked in slice 01, git status shows the package as ?? (with the engine update inside); this is consistent with prior slice and not a scope issue. (The test diff is cleanly tracked.)
- No issues with the prior plan prose fix (18→25) affecting this slice; the engine correctly handles the 25 mappings from the seed.

**Workflow compliance:** Excellent. Followed claiming exactly (move before edits), discovery, exact steps, smoke-only policy, output artifacts (including raw command outputs and scope confirmation), and cleanup of only the claimed in-progress file. No scope creep or out-of-scope edits attempted. "Stop and document + follow-up prompt" rule not needed.

---

## Recommendation

**Accept / land the slice.**

This slice successfully delivers the real, lightweight CategoryTree engine with working classify() as the core of Phase 1. It is standalone, testable, matches the approved plan's design exactly where specified, follows the lightweight priority, keeps the hot path clean (no LLM/I/O), and adds the required smoke test. All smoke + manual verifications pass. It is a clean, explicit, reviewable step forward — ready for slice 03 (supervisor injection).

No immediate follow-up prompt required from this review. Cursor's "Ready for slice 03" note aligns with the plan.

(Review written after reading the full slice 02 prompt, Cursor's output.md + prompt.md, the current engine.py / models.py / test_supervisor_routing.py in full, the authoritative `docs/plans/classification-engine-phase1.md` (Detailed Design section, classify sketch, Step 2 verifs, lightweight note, _SEED, risks), re-running every verification command + ruff/smoke/LLM grep/fidelity checks, confirming git diffs limited to scope, and verifying literal match to the plan's implementation sketches.)

---

**Project state after this slice:** The classification engine now has real fast classify() for known/unknown attributes (25 mappings from seed). Existing smoke tests (including new one) green. No public API or query behavior changes yet. Next is wiring into supervisor per slice 03.
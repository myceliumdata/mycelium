# Task: Classification Engine Phase 1 - Slice 02: Implement core CategoryTree engine (lightweight)

**Read these first (mandatory):**
- `docs/plans/classification-engine-phase1.md` (the approved plan - immutable spec. Focus on "Detailed Design of CategoryTree Class / Module", the Pydantic models, "Initial Seed Content", the lightweight priority note, Step 2 verification commands, and the risks around cache/unknowns)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`

**Objective**
Implement the core CategoryTree (the "brain") per the approved plan's detailed design. This is the lightweight version: simple .write_text for _save (atomic only in later polish if the diff stays small), full classify (fast in-memory lookup by normalized name, "unknown" with confidence 0.0 for missing - never LLM or I/O on hot path), the _SEED_CATEGORIES constant, get/reset, etc. refresh_from_llm is a stub. Add a basic smoke test for classify/unknown.

This slice delivers a standalone, testable classification engine. No wiring to supervisor/state yet (that is slice 03). Follow the lightweight priority strictly.

**Lightweight priority (from approved plan - obey)**
"Keep implementation as lightweight as possible in early steps. Prioritize getting `classify()` + supervisor injection working cleanly before polishing `refresh_from_llm` and atomic saves. Err on the side of simplicity for Phase 1."

For this slice: plain write_text for _save, no tempfile yet, no full refresh logic, explicit readable code.

**Constraints & Principles**
- Strictly limited scope (see box).
- The implementation must match the sketches in the approved plan exactly (copy the _SEED, the classify logic for unknown/known, the module level get/reset, etc.).
- Small, reviewable.
- Smoke -q default.
- This is slice 02 of the small sequence (the big prompt in next/ is superseded).

**Context**
- Slice 01 (scaffold) has created the data/categories.json and the package skeleton.
- The approved plan has the exact _SEED_CATEGORIES literal, the CategoryTree methods, the ClassificationResult for unknown, and the test verification (python -c classify email/spouse/unknown, smoke).
- Current hot path must never call LLM (enforced in this and later slices by grep in final, and no import of ChatOpenAI in hot path code).
- The engine must support the env MYCELIUM_CATEGORIES_PATH (like storage and checkpoints).
- Later slices will wire it to supervisor (03), propagate (04), and refresh (05).

See approved plan "Detailed Design of CategoryTree", "Safe Mechanism..." (for the refresh stub), and "Risk / Mitigation" (especially unknown and cache).

**Exact Steps (perform in order)**
1. **Claim first**: Move this file from next/ to in-progress/ (per WORKFLOW). Document in output.

2. **Discovery**: Read the approved plan sections listed above. Read the current classification/ files (from slice 01) to see the stubs. Run the repro from slice 01 if needed. Confirm `data/categories.json` exists with the seed.

3. **Implement models.py** (if not complete from slice 01, make sure it matches the approved "Pydantic Models" section exactly, including CategoryProposal for the future refresh stub).

4. **Implement engine.py** (the main work, matching the approved sketch):
   - Add the necessary imports (json, os, tempfile if you choose for later, but keep simple: use plain write for now).
   - The _SEED_CATEGORIES exact from approved.
   - _default_categories_path using MYCELIUM_CATEGORIES_PATH.
   - CategoryTree class with:
     - __init__ setting cache_path and calling _load
     - _load: if file exists load + model_validate, else _create_seed + _save
     - _save: simple self.cache_path.write_text( self._data.model_dump_json(indent=2) )  -- per lightweight (no atomic yet)
     - _create_seed: return CategoryTreeData.model_validate(_SEED_CATEGORIES)
     - reload, classify (the exact logic: normalize lower, if not in map return unknown result with category="unknown", confidence=0.0; else look up and return with 0.95)
     - get_categories
     - (stub) refresh_from_llm that returns {"reason": "implemented in slice 05"} or raises clear NotImplemented with comment referencing approved plan
   - The module level _category_tree = None, get_category_tree(), reset_category_tree() exact from approved sketch.
   - Add clear comments: "Lightweight per approval note: simple save. Atomic in polish slice if small. LLM only in refresh (slice 05). classify is pure lookup."
   - Make sure classify never does I/O or LLM after load.

5. **Update test for smoke (narrow)**: In `tests/test_supervisor_routing.py` (or the minimal addition), add a smoke test that exercises the engine directly (using a temp path or the default, but since env not set in smoke, it will use data/ which is fine for smoke). Something like:
   ```python
   @pytest.mark.smoke
   def test_classification_engine_basic():
       from agents.classification import get_category_tree, reset_category_tree
       reset_category_tree()
       t = get_category_tree()
       r = t.classify("email")
       assert r.category == "contact"
       assert r.assigned_agent == "contact_specialist"
       assert r.confidence > 0.9
       u = t.classify("foo_unknown")
       assert u.category == "unknown"
       assert u.confidence == 0.0
   ```
   (Keep the test minimal and in the existing smoke file.)

6. **Verification (smoke + manual for this slice)**:
   - `uv run pytest -m smoke -q`
   - The manual from approved Step 2:
     `uv run python -c '
     from agents.classification import get_category_tree, reset_category_tree
     reset_category_tree()
     t = get_category_tree()
     print(t.classify("email"))
     print(t.classify("spouse"))
     print(t.classify("weird_unknown"))
     ' `
     (must show contact, relationships, unknown; no errors).
   - Confirm `git status` or diff shows changes only in classification/ files + the test file addition.
   - Confirm no "ChatOpenAI" or real LLM code in the engine (grep in your verification).

7. **Output artifacts**:
   - done/ dir with output.md (summary, decisions e.g. "kept _save as plain write_text per lightweight", full command outputs, diffs for the changed files in this slice, scope confirmation).
   - prompt.md copy.
   - Remove only your claim from in-progress/.

**Scope Boundaries (Strict)**
You may only modify/create:
- `src/agents/classification/models.py`
- `src/agents/classification/engine.py`
- `tests/test_supervisor_routing.py` (only the addition of the basic classify smoke test)

**Out of Scope (Do Not Touch)**
- data/ (already done in slice 01)
- `src/models/state.py`, `src/agents/supervisor.py`, core_data, responses, graphs, mcp, main, storage, other tests, docs, the superseded big prompt, the approved plan, TODO.md, etc.
- Any implementation of refresh_from_llm logic or atomic save (lightweight: simple for now).
- Do not wire classify into supervisor (slice 03).

If out of scope needed: stop, document, create follow-up prompt.

**Test Execution Policy**
- `uv run pytest -m smoke -q`
- The new test is smoke (pure, no DB, no graph invoke).
- If you think it needs full marker, document for Grok.

**Required Output**
`prompts/cursor/done/2026-06-03-classify-02-engine/output.md` etc. per WORKFLOW.

Follow claiming before any edit.

After delivery, we will review just this slice (re-run the classify python -c and smoke, check diffs are only in scope, confirm lightweight followed, confirm classify works for known/unknown, add review.md, then prepare slice 03).

Claim and go - small, explicit, per the approved plan sketches.
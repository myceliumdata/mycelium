# Task: Classification Engine - Wire LLM into classify() for unknown attributes (handle garbage safely)

**Read these first (mandatory):**
- `docs/plans/classification-engine-phase1.md` (the approved plan - note the original design kept classify as pure lookup with "unknown" for missing, LLM *only* in off-path refresh_from_llm. This new work extends it.)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`

**Objective**
Extend the `classify()` method in `CategoryTree` so that for attributes not in the map (i.e. "unknown"), it wires in an LLM call (using the same style as refresh_from_llm: lazy ChatOpenAI, structured output with CategoryProposal or similar, conservative) to attempt to classify the unknown attribute on the fly. 

The goal is to classify "unknown" attributes intelligently instead of always returning category="unknown" with confidence=0.0.

Critically, deal with garbage input like "foo_bar_baz" (random strings, nonsense, etc.) by having the LLM (via careful prompt) decide it's "unknown" with low or appropriate confidence, without polluting the taxonomy with bad mappings. Only add/cache a mapping if the LLM is confident it's a real category (existing or new sensible one).

This should be safe: LLM only triggered for first-time unknowns (then cached in the map like refresh does), keep hot path fast for knowns, no breakage to existing behavior.

**Lightweight priority**
Keep changes minimal. Reuse as much as possible from the existing refresh_from_llm logic/prompt (don't duplicate code if possible; perhaps factor a helper). Follow the conservative rules from the plan (conf >=0.7 to act, etc.).

**Constraints & Principles**
- Strictly follow the spirit of the approved plan where possible, but implement the requested extension for on-the-fly classification of unknowns.
- LLM call must be lazy (no top-level import of langchain_openai in the module).
- Prompt must explicitly instruct the LLM to treat garbage/nonsense/random strings (e.g. "foo_bar_baz", "asdf123", obviously invalid attr names) as "unknown".
- For garbage, return the "unknown" ClassificationResult (confidence 0.0 or LLM's), and do *not* add it to the map (or add as special "unknown" if needed, but keep clean).
- If LLM proposes a good category (existing or new) with high confidence, update the in-memory map + persist via _save (so future classifies are fast lookup), then return the result.
- Preserve exact current behavior for all known attributes.
- For unknowns that LLM can't confidently classify (low conf, garbage), fall back to current "unknown" result.
- No changes to hot-path callers (supervisor etc.) - they just get better results for what used to be unknown.
- Add/update tests (smoke-safe, mock the LLM like in slice 05).
- Update relevant docs/comments if high value (e.g. in engine.py, architecture.md if needed).
- Run smoke + relevant full tests + manual CLI checks at end.
- Follow all prior constraints: small/reviewable, explicit, etc.

**Context**
- Current classify() is pure dict lookup (per Phase 1 plan). Unknowns always return category="unknown", confidence=0.0, description="No classification available...". This works for garbage but doesn't "classify" them intelligently.
- refresh_from_llm already has the LLM wiring, prompt, structured CategoryProposal, conservative merge logic, lazy import, _save etc.
- The plan warned about garbage unknowns and kept LLM off hot path, but now we want to wire LLM specifically for the unknown case in classify() to handle them better (auto-evolve good ones, safely reject garbage).
- This will make first unseen (but classifiable) attrs get LLM-classified on first use, cached thereafter.
- Garbage like "foo_bar_baz" must not get mapped to a real category; LLM prompt + logic must ensure it stays "unknown".
- Existing tests, CLI behavior, etc. must continue to work (just improve for unknowns).
- Use the same model/temp=0 as refresh.

See the current classify(), refresh_from_llm(), _SEED_CATEGORIES, CategoryProposal, etc. in src/agents/classification/engine.py. Also how it's used in supervisor, responses, tests.

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, this should be the next/oldest, **immediately move** it to `prompts/cursor/in-progress/2026-06-03-classify-07-llm-unknowns/prompt.md`. Only then begin work. Document the move in your output.md.

2. **Discovery (read-only)**:
   - Read the approved plan (note original no-hot-path-LLM for classify).
   - Read current `src/agents/classification/engine.py` (classify, refresh_from_llm, prompt, models, _save, etc.).
   - Read `src/agents/classification/models.py` (CategoryProposal).
   - Read relevant tests: `tests/test_supervisor_routing.py` (the classify and refresh tests).
   - Read `tests/test_core_graph.py` (non-core tests that check debug for classifications).
   - Read `src/agents/supervisor.py` (how it calls classify).
   - Run baseline: `uv run pytest -m smoke -q`, and a manual `uv run python -c 'from agents.classification import get_category_tree, reset_category_tree; reset_category_tree(); t=get_category_tree(); print(t.classify("foo_bar_baz")); print(t.classify("email"))' ` to see current "unknown" behavior.
   - Confirm `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes foo_bar_baz` shows "unknown" in debug.

3. **Implement the wiring in classify()**:
   - Modify `classify()` so that when `normalized not in self._data.attribute_map` (current unknown case):
     - Call the LLM (reuse logic from refresh_from_llm: lazy ChatOpenAI if needed, the prompt adapted for *single* attr, with_structured_output(CategoryProposal), etc.).
     - Enhance/adapt the prompt to explicitly handle garbage: instruct LLM that for nonsense/garbage/random like "foo_bar_baz", "asdf123!", obviously invalid, return category="unknown" (high confidence for that decision).
     - If LLM returns a proposal with confidence >=0.7 and category != "unknown" (and it's a sensible one):
       - If new category, add it to self._data.categories (like refresh does).
       - Set self._data.attribute_map[normalized] = cat_name.
       - Call self._save(); self._load().
       - Then return the ClassificationResult using the (new) cat (with the LLM's confidence, or 0.95 like before?).
     - Else (garbage, low conf, or LLM said "unknown"):
       - Optionally cache normalized -> "unknown" in map (to avoid repeated LLM calls for same garbage next time), then _save/_load.
       - Return the standard "unknown" ClassificationResult (confidence 0.0).
   - Keep the fast path for known attrs 100% unchanged (pure lookup, no LLM, 0.95 conf).
   - Make LLM lazy (import inside the unknown branch, like refresh).
   - Add clear comments: "Wired LLM for first-time unknown attrs only (via refresh-style logic). Garbage like foo_bar_baz is rejected by prompt + logic. Subsequent calls are cached lookup."
   - Do not change the public API or ClassificationResult shape.

4. **Update the shared prompt/logic if needed**:
   - If it makes sense, factor out a small private helper (e.g. _llm_propose_category(attr: str) -> Optional[CategoryProposal]) that both refresh_from_llm and the new classify path can use, to avoid duplication. Keep it internal.
   - Update the prompt text (the one used in refresh) to better emphasize garbage rejection (as in objective), since it will now also be used for on-the-fly classify.
   - Keep the conservative rules (0.7 threshold, additive, etc.).

5. **Add/update tests (smoke-safe)**:
   - In `tests/test_supervisor_routing.py` (or appropriate smoke file): add tests for the new behavior.
     - Test that known attrs still pure/fast (no LLM).
     - Test unknown/garbage like "foo_bar_baz" still ends as "unknown" 0.0 (use mock LLM that returns "unknown" proposal).
     - Test a sensible unknown (e.g. "net_worth") gets LLM-classified to a new/existing cat with high conf, added to map, subsequent classify is fast lookup (use mock LLM).
     - Ensure tests use mocks / tmp_path, no real LLM or OPENAI key.
   - Make sure existing tests (including refresh, non-core, etc.) still pass and where relevant assert on the improved behavior for what used to be unknowns.
   - Update any direct engine tests.

6. **Update comments/docs**:
   - In engine.py: update module docstring and classify/refresh docstrings to reflect the new on-demand LLM for unknowns.
   - Optionally small update in `docs/architecture.md` or the plan if high value (but keep minimal; reference the new behavior).
   - Ensure the "LLM only in refresh..." comments are updated to note the controlled use inside classify for unknowns.

7. **Verification**:
   - `uv run pytest -m smoke -q`
   - `uv run ruff check src/agents/classification tests/test_supervisor_routing.py`
   - Manual:
     - `uv run python -c 'from agents.classification import get_category_tree, reset_category_tree; reset_category_tree(); t = get_category_tree(); print(t.classify("email")); print(t.classify("foo_bar_baz")); print(t.classify("net_worth"))' ` (with mocks in test, but for manual use the mock test or note).
     - `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes foo_bar_baz` (should still "unknown" in debug).
     - `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes net_worth` (if using real or after mock, should get classified).
     - Re-run some non-core queries to confirm classifications appear for previously unknown but now classified attrs.
   - Confirm no hot-path LLM for known attrs (the LLM only in the unknown branch).
   - Confirm garbage is safely "unknown".
   - `uv run python -c '...' ` to test caching (first classify unknown triggers "LLM", second is fast).
   - Grep to confirm LLM usage is only in the intended places.
   - Ensure the change is small/reviewable.

8. **Output artifacts**:
   - Create `prompts/cursor/done/2026-06-03-classify-07-llm-unknowns/output.md` with:
     - Summary of changes (the wiring in classify, prompt update for garbage, helper if added, tests, docs/comments).
     - Full outputs of verification commands.
     - Diffs (git diff for the changes in this slice).
     - Confirmation that known attrs unchanged, garbage safely unknown, sensible unknowns get auto-classified + cached, all tests pass, behavior matches request.
   - Move/copy this prompt into done/ as prompt.md.
   - Remove only the claimed file from in-progress/.

**Scope Boundaries (Strict)**
You may only modify/create:
- `src/agents/classification/engine.py` (classify logic, prompt update, comments/docstrings, optional helper)
- `tests/test_supervisor_routing.py` (new/updated smoke tests for the feature)
- Possibly small comment/doc updates in `docs/architecture.md` or engine.py (high value only)

**Out of Scope (Do Not Touch)**
- Anything that would make LLM calls for *known* attributes.
- Changes to supervisor, core_data, responses, state, graphs, mcp, main, other tests (except adding to existing smoke file as above).
- Large refactors or changes to refresh_from_llm beyond what's needed for reuse.
- Editing the approved plan or creating new plans.
- Anything outside the narrow "wire LLM for unknowns + handle garbage" request.

If you determine changes outside this are needed: **Stop immediately**, document in output.md, create a follow-up prompt instead of making the change.

**Test Execution Policy**
- Default smoke -q.
- The new tests must be smoke (mocked, no real LLM/key).
- Run smoke after changes.
- If touching full tests, run them (but scope limits to the smoke file).

**Required Output Location & Artifacts**
- `prompts/cursor/done/2026-06-03-classify-07-llm-unknowns/output.md`
- The claimed prompt moved to done/ as prompt.md

Follow the claiming process in WORKFLOW.md exactly before any implementation.

This extends the Phase 1 engine to intelligently handle unknowns via LLM while safely rejecting garbage. Make the change small, explicit, and reviewable. Use mocks for tests. Reference the plan and prior slices for style/consistency.

Claim the file (move to in-progress/) and execute. Good luck.
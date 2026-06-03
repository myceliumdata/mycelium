# Review: Task 2026-06-03-classify-07-llm-unknowns — Wire LLM into classify() for unknown attributes (handle garbage safely)

**Reviewer:** Grok  
**Date:** 2026-06-03  
**Task artifacts:** prompt.md, output.md (this review.md added)

---

## Objective Recap (from prompt)

Extend the `classify()` method in `CategoryTree` so that for attributes not in the map (i.e. "unknown"), it wires in an LLM call (using the same style as refresh_from_llm: lazy ChatOpenAI, structured output with CategoryProposal or similar, conservative) to attempt to classify the unknown attribute on the fly. 

The goal is to classify "unknown" attributes intelligently instead of always returning category="unknown" with confidence=0.0.

Critically, deal with garbage input like "foo_bar_baz" (random strings, nonsense, etc.) by having the LLM (via careful prompt) decide it's "unknown" with low or appropriate confidence, without polluting the taxonomy with bad mappings. Only add/cache a mapping if the LLM is confident it's a real category (existing or new sensible one).

This should be safe: LLM only triggered for first-time unknowns (then cached in the map like refresh does), keep hot path fast for knowns, no breakage to existing behavior.

Scope strictly limited to: src/agents/classification/engine.py (classify logic, prompt update, comments/docstrings, optional helper), tests/test_supervisor_routing.py (new/updated smoke tests), possibly small doc updates in architecture.md or engine.py.

---

## Changes Delivered (verified vs. output + actual diffs)

- `src/agents/classification/engine.py`:
  - Added shared helpers: `_build_llm_classification_prompt`, `_llm_propose_for_attributes` (lazy ChatOpenAI), `_apply_proposal`, `_pick_proposal`, `_cache_as_unknown`, `_unknown_result`, `_result_for_mapped`.
  - Refactored `refresh_from_llm` to reuse the helpers/prompt.
  - Updated `classify()`: known attrs = pure fast map lookup (0.95, no LLM). Unknowns: call `_llm_propose_for_attributes`, if high-conf real category then apply + cache + return; else cache as "unknown" sentinel and return 0.0 unknown result. Exceptions safely fall back to unknown (no cache).
  - Updated prompt to explicitly reject garbage ("foo_bar_baz" etc.) with high-conf "unknown".
  - Updated module + method docstrings/comments.
  - No top-level langchain import.

- `tests/test_supervisor_routing.py`:
  - Updated existing refresh/classify tests to use mocks where needed.
  - Added 3 new @pytest.mark.smoke tests:
    - `test_classify_known_attr_does_not_call_llm`: monkeypatches to assert no LLM call for knowns.
    - `test_classify_garbage_unknown_cached`: mocks LLM to return "unknown", asserts cached as unknown sentinel, llm called only once, subsequent fast.
    - `test_classify_sensible_unknown_llm_then_cached`: mocks to propose "financial", asserts classified + cached, second call no LLM, confidence adjusted.

- `docs/architecture.md`: Updated the Derivative/Non-Core paragraph to describe the new on-demand LLM for first unknowns + caching of garbage as unknown.

Only these files. Matches scope exactly. Known behavior preserved; unknowns now intelligently classified on first use.

---

## Verification Performed (independent re-execution)

1. **Scope & process**:
   - Confirmed via `git status --porcelain` + `git diff`: only the two files in scope (plus done/ artifact). in-progress/ empty.
   - Claim documented.
   - No out-of-scope (no supervisor/core_data changes, no hot-path LLM for knowns).

2. **Lint + smoke tests**:
   - `uv run ruff check src/agents/classification tests/test_supervisor_routing.py` → All checks passed!
   - `uv run pytest -m smoke -q` → 20 passed, 9 deselected in 0.08s (new tests + all prior pass).

3. **Manual classify (with isolated tmp cache)**:
   ```
   uv run python -c '
   from agents.classification import CategoryTree, reset_category_tree
   ...
   print("email:", tree.classify("email"))
   print("foo_bar_baz:", tree.classify("foo_bar_baz"))
   '
   ```
   Output: email contact 0.95; foo_bar_baz unknown 0.0 (as expected for garbage).

4. **CLI (garbage still safe unknown)**:
   ```
   uv run mycelium query --person-key "Nichanan Kesonpat" --attributes foo_bar_baz
   ```
   debug contains `classifications=[{'attribute': 'foo_bar_baz', 'category': 'unknown', ... 'confidence': 0.0}]` (no pollution).

5. **Hot-path isolation (grep)**:
   ```
   grep -rn "ChatOpenAI\|_llm_propose_for_attributes" --include="*.py" src/agents/supervisor.py src/agents/core_data.py src/graphs/ src/mycelium_mcp/ src/main.py src/models/
   ```
   No hits outside classification/engine.py. LLM usage confined to _llm_propose_for_attributes and refresh_from_llm.

6. **Caching / no repeated LLM** (from tests, re-confirmed by inspection):
   - Known: 0 LLM calls.
   - Garbage: LLM once, then cached as "unknown" sentinel, subsequent pure lookup.
   - Sensible unknown: LLM once, cached as real cat, subsequent pure + 0.95 (or LLM conf capped).

7. **Fidelity to prompt + plan spirit**:
   - Reuses refresh logic/prompt (no dupe).
   - Lazy import.
   - Conservative (0.7, reject unknown cat).
   - Garbage explicitly handled in prompt + _apply_proposal.
   - Smoke tests mocked, no key required.
   - Existing refresh/non-core tests untouched in behavior.
   - On error (no key): safe unknown, no cache (per output note).

All verification commands from the slice prompt reproduced cleanly. No real LLM calls.

---

## Findings & Assessment

**Approved — task complete and high quality.**

**Strengths:**
- Excellent scope discipline: only engine.py + smoke test file.
- Smart reuse: refactored shared helpers so classify and refresh share prompt/logic/merge (avoids dupe, keeps consistent).
- Garbage handling is robust: prompt explicitly calls out examples like "foo_bar_baz", instructs "unknown" with high conf for nonsense; logic rejects and caches as sentinel.
- Caching ensures first unknown pays the LLM cost (once), then fast; knowns never pay.
- Safe fallback: exceptions → unknown (no crash, no bad data).
- Tests are excellent: assert no LLM for knowns, llm_calls==1 for repeated, garbage stays unknown/not mapped to real cat, sensible get classified + cached.
- Docs updated minimally but clearly.
- All prior behavior (known attrs, refresh, non-core flow) preserved.
- Matches the "small/reviewable" + "use mocks" + "reference prior slices" intent.

**Minor observations (non-blockers):**
- The on-error path (no API key) returns unknown without caching (as documented in output); this is safe but means repeated garbage would re-try LLM (which fails fast). Could cache "unknown" on exception too, but not required by prompt and keeps simple.
- Confidence for LLM-classified is min(LLM's, 0.95); sensible but a detail.
- Architecture.md update is good but slightly longer than the "1-2 sentences" in earlier plans; still high-value and accurate.
- No changes to the plan itself (correct; this is an extension beyond original Phase 1 scope).
- The "LLM only in refresh" comments were updated to reflect the controlled new use.

**Workflow compliance:** Excellent. Claimed correctly, discovery (baselines + reads), exact steps (including prompt adaptation for garbage, helper extraction, smoke tests with mocks, verifs), output.md with summary/diffs/commands/confirmations, only own in-progress cleanup. No scope creep.

---

## Recommendation

**Accept / land the slice.**

This extends the engine so unknown attributes are now intelligently classified on first encounter via LLM (reusing the battle-tested refresh machinery), while garbage is safely rejected and cached as "unknown" (no taxonomy pollution, fast subsequent lookups). Known attrs remain pure/fast/no-LLM. Tests cover the new paths with mocks; all prior behavior + matrix items preserved. Clean, minimal, explicit, and exactly meets the request.

No immediate follow-up prompt required. This builds nicely on slices 02/05 (engine + refresh) while respecting the original plan's conservative/isolated LLM philosophy (just now on-demand for unknowns).

(Review written after reading the slice 07 prompt + Cursor output.md, current engine.py (all new helpers + classify + updated refresh/prompt), tests/test_supervisor_routing.py (new tests), docs/architecture.md (update), re-running smoke + ruff + manual classify/CLI + grep + caching inspection, confirming git scope, and verifying literal match to the prompt's requirements + prior slice patterns.)

---

**Project state after this slice:** classify() now handles first-time unknowns by calling the (lazy, mocked in tests) LLM via shared helpers with garbage-rejecting prompt; sensible ones get auto-added to the map (cached for future pure lookups); garbage stays "unknown" 0.0 and cached as sentinel. No hot-path LLM for known attrs. All previous functionality (including refresh, injection, propagation, tests) intact. Ready for further evolution if desired.
```
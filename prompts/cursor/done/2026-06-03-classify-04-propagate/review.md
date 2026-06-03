# Review: Task 2026-06-03-classify-04-propagate — Propagate classifications into core_data, responses, and full test isolation

**Reviewer:** Grok  
**Date:** 2026-06-03  
**Task artifacts:** prompt.md, output.md (this review.md added)

---

## Objective Recap (from prompt)

Make the classification metadata visible in the PersonResponse (via debug) and the final graph state. Update core_data_agent to forward the classifications from incoming state into the payload. Update responses.py (debug_for_query or the builder calls) to include the classifications info in the debug string. Update the temp_storage fixture and non-core tests in test_core_graph.py to set MYCELIUM_CATEGORIES_PATH, reset the category tree, and assert the metadata appears for non-core requested attrs.

This completes the end-to-end for metadata in results for the current core_data path. Previous slice (03) made it appear in audit from supervisor; this makes it in the user-visible response.debug.

Scope strictly limited to: src/agents/core_data.py, src/agents/responses.py, tests/test_core_graph.py.

---

## Changes Delivered (verified vs. output + actual diffs)

- `src/agents/core_data.py`: In _build_lookup_response, capture classifications = state.classifications or None, pass via **clf_kwargs to response_* builders. In _run_core_data_lookup, always include "classifications": state.classifications in the payload dict (forwarded to final state).

- `src/agents/responses.py`: Added _debug_extra_value using repr(value) for any type. Updated debug_for_query to accept **extra: Any and include f"{key}={_debug_extra_value(value)}". All three response_* builders (found, not_found, non_core) now accept optional classifications: list[dict[str, Any]] | None = None, and conditionally pass **({"classifications": classifications} if classifications else {}) to debug_for_query.

- `tests/test_core_graph.py`: In temp_storage fixture: import and call reset_category_tree() in setup/teardown, add monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", ...). In test_query_non_core_attributes: assert "classifications=" in response.debug, plus "demographic" and "social" (from the attrs used).

Only these three files. Matches the approved plan's propagation notes exactly (forward in payload, thread via extra to debug, fixture updates for isolation).

---

## Verification Performed (independent re-execution)

1. **Scope & process**:
   - Confirmed via `git status --porcelain` and `git diff`: only the three files in scope modified (+ done/ artifact). in-progress/ is empty.
   - Claim documented in output.md.
   - No out-of-scope files (classification/, state, supervisor, etc. untouched).
   - Discovery followed (read plan, core_data, responses, test_core_graph, baseline runs).

2. **Lint + tests (per prompt policy)**:
   - `uv run pytest -m smoke -q` → 15 passed, 9 deselected in 0.05s.
   - `uv run pytest -m full -q -k "non_core or query_non_core"` → 1 passed, 23 deselected in 0.06s (the key non-core test passes and now includes classifications evidence).
   - ruff on the three files: All checks passed!

3. **Manual CLI queries (exact from slice prompt + plan)**:
   - `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email`:
     ```
     "debug": "...; classifications=[{'attribute': 'email', 'category': 'contact', 'assigned_agent': 'contact_specialist', 'description': 'Direct ways to reach the person (email, phone, physical).', 'confidence': 0.95}]"
     ```
     (Metadata now in .debug, as required. Message still "still researching".)
   - `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes foo_bar_baz` (unknown):
     ```
     ... classifications=[{'attribute': 'foo_bar_baz', 'category': 'unknown', 'assigned_agent': None, 'description': 'No classification available for this attribute.', 'confidence': 0.0}]
     ```
   - `uv run mycelium query --person-key "Kevin Zhang" --attributes x_handle` (ambiguous + attr):
     ```
     num_matches='2'; classifications=[{'attribute': 'x_handle', 'category': 'social', ... 'confidence': 0.95}]
     ```
     (Classifications appear even for multi-result; correct category.)

4. **Test assertions and fixture isolation**:
   - In test_query_non_core_attributes: asserts "classifications=" , "demographic", "social" in debug (for "age", "x_handle").
   - Fixture properly resets category tree and sets isolated MYCELIUM_CATEGORIES_PATH (no pollution of committed data/categories.json).
   - Core-only queries (e.g. test_query_existing_person) still pass without classifications in debug.

5. **Fidelity to plan**:
   - Payload forward + debug threading via extra matches the "Propagation to result / observability" section exactly.
   - No changes to PersonResponse shape, routing, or core logic.
   - Engine from prior slices used (classifications from supervisor flow through).

All verification commands from the slice prompt and plan Step 4 reproduced cleanly. Full targeted tests run as required by policy.

---

## Findings & Assessment

**Approved — task complete and high quality.**

**Strengths:**
- Precise adherence to narrow scope (only 3 files).
- Changes are minimal and directly implement the approved plan's propagation notes (classifications captured in core_data, passed via **extra to debug_for_query in builders).
- debug_for_query enhancement with repr() is clean and general (handles lists/dicts without breaking existing string asserts like "non_core_requested=...").
- Fixture updates follow exact pattern from other MYCELIUM_*_PATH + resets (good isolation).
- Non-core test now asserts the new metadata (plus existing behavior).
- All manual queries (known, unknown, ambiguous) now surface classifications in .debug as specified.
- Lightweight: no over-engineering, no public API changes, preserves all prior messages/outcomes.

**Minor observations (non-blockers):**
- In core_data.py, "classifications" is always put in payload (even if empty list or None); this is fine and matches the "include in the returned payload dict" note. Builders only include in debug when truthy.
- The test uses "age, x_handle" which map to demographic/social, and asserts the category names appear in debug (via the repr of the list); this is a solid indirect check.
- repr() makes the debug string contain the full list with quotes etc.; the assert "classifications=" is sufficient per the prompt.
- No issues with prior date fixes or 18/25 plan correction; everything consistent.
- The CLI debug now includes the full classifications list (as in the output.md example).

**Workflow compliance:** Excellent. Followed claiming, discovery (reads + repros), exact steps for code + fixture + test, smoke + full targeted tests, output artifacts with commands/diffs/scope, only own in-progress cleanup. No scope creep. Matches "small/reviewable" and "run the full marker for new full tests" policy.

---

## Recommendation

**Accept / land the slice.**

This slice completes the propagation: classifications now flow end-to-end from supervisor (slice 03) through core_data into PersonResponse.debug (and full graph state). Non-core queries (including unknowns and ambiguous names) now expose the metadata in .debug exactly as planned. Full tests and manuals pass with evidence. Clean, minimal, faithful to the approved plan's Step 4 notes. Ready for slice 05 (refresh_from_llm, off-path only).

No immediate follow-up prompt required from this review. Cursor's "Ready for slice 05" note aligns with the plan.

(Review written after reading the slice 04 prompt, Cursor's output.md + prompt.md, current core_data.py / responses.py / test_core_graph.py + diffs, the authoritative `docs/plans/classification-engine-phase1.md` (Step 4 propagation section, verification commands, lightweight note), re-running smoke + full targeted + all manual queries from the prompt/plan, confirming git scope, and verifying exact match to propagation requirements.)

---

**Project state after this slice:** Classifications from supervisor are now forwarded in core_data payload and appear in response.debug for non-core attrs (known: category/assigned_agent/conf; unknown: explicit "unknown"/0.0). Full non-core graph tests assert it. Audit from 03 + debug from 04 now both visible. Still no routing changes. Next: refresh path (slice 05).
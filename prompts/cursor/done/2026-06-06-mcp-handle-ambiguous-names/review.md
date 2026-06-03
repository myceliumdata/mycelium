# Review: Task 2026-06-06-mcp-handle-ambiguous-names — Support multiple results for ambiguous names (Kevin Zhang)

**Reviewer:** Grok  
**Date:** 2026-06-06  
**Task artifacts:** prompt.md, output.md (this review.md added)

---

## Objective Recap
Fix the core lookup so that `person_key` (name) matching multiple distinct people (same name, different `employer`) returns *all* of them in `PersonResponse.results`. The seed intentionally keeps two "Kevin Zhang" entries (Bain Capital Ventures + Upfront Ventures). Previously `find_person` + `fetchone()` + single-person paths meant only the first was ever returned.

Changes limited to the explicitly listed files. Preserve all prior behavior for unique names/IDs, no new models, plural-aware messages, compat for `person` field in state/payload for tests/legacy.

---

## Changes Delivered (verified vs. output + actual diffs)

- `src/storage/core.py`: `find_person` → `find_persons` returning `list[Person]`. Name query now uses `fetchall()` + `ORDER BY id` (deterministic). ID match still returns 0/1 wrapped in list.
- `src/agents/core_identity.py`: `find_by_key` now returns `list[Person]`, delegates to `find_persons`. Updated docstring.
- `src/agents/responses.py`: `response_found` and `response_non_core` now take `persons: list[Person]`. Build results list, choose singular/plural message, add `num_matches` to debug. `response_not_found` unchanged.
- `src/agents/core_data.py`: Updated `_build_lookup_response` to return `list[Person]`. `_run_core_data_lookup` always sets `"persons"`, sets `"person"` only on exactly 1 match (compat). Uses the list versions of builders.
- `src/agents/routing.py` (legacy, test-only): `SupervisorDecision` now has `persons: list[Person]` + compat `person`. `evaluate_supervisor_turn` updated symmetrically.
- `src/models/state.py`: Added `persons: list[Person] = Field(default_factory=list)`. Kept `person` for compat. Docstring lightly updated.
- `tests/test_core_data_agent.py` + `tests/test_supervisor_routing.py`: Stub `find_by_key` now returns `list[Person]`. Existing single-person asserts continue to pass thanks to compat `"person"` field.
- `docs/architecture.md`: Updated lookup table row to document "one or more".
- `docs/full-code-walkthrough.md`: Updated sections 5/7/8/9 to reflect 0/1/N and `find_persons`.

All changes small and focused (76 insertions, 53 deletions across 10 files).

---

## Verification Performed (independent)

1. **Scope & process**:
   - Only the 10 files listed in the prompt were modified (confirmed via `git diff --name-only`).
   - in-progress/ cleaned (only this task's file removed).
   - Claim documented in output.md.
   - No other files touched (e.g. server.py, main.py, graphs, enrich/validator, README, TODO, health_check, etc.).

2. **Lint + smoke tests**:
   - `uv run ruff check` (on changed files) → All checks passed.
   - `uv run pytest -m smoke -q` → 13 passed (matches Cursor output).

3. **Functional repro (user-reported case)**:
   - `uv run mycelium query --person-key "Kevin Zhang"`
     - Results: exactly 2 entries (person-0058 Bain, person-0438 Upfront) in insertion/ID order.
     - Message: "Found 2 core records for 'Kevin Zhang'."
     - Debug: contains `num_matches='2'`, `outcome='found'`.
   - With `--attributes email`:
     - Same 2 results.
     - Message: "We have 2 core records for 'Kevin Zhang', but we're still researching email."
     - Debug has `non_core_requested`, `num_matches='2'`.
   - Unique name still singular: "Nichanan Kesonpat" → 1 result, "Found core record for Nichanan Kesonpat.", `num_matches='1'`.
   - Not-found still works (empty results, singular message).

4. **Internal payload / state**:
   - For single match: both `"persons": [..]` (len 1) and `"person": <first>` are set.
   - For 0 matches (not-found): neither `"persons"` nor `"person"` set → existing test `assert "person" not in result` passes.
   - For 2 matches: `"persons"` set (len 2), `"person"` not set (compat behavior).
   - `MyceliumGraphState` now has `persons` attribute.

5. **Legacy path**:
   - `evaluate_supervisor_turn` (used by routing tests) updated and exercises the same list logic. Existing routing smoke tests (which use single-person stubs) still pass.

6. **Docs**:
   - Architecture table and walkthrough updated to reflect multi-match support. No over-claiming.

7. **Other**:
   - `git status` clean for the task (the done/ dir is the artifact).
   - No behavior change for ID lookups or unique names.
   - Order deterministic thanks to `ORDER BY id`.

All verification commands in Cursor's output.md reproduced cleanly.

---

## Findings & Assessment

**Approved — task complete and high quality.**

**Strengths:**
- Excellent adherence to strict scope boundaries.
- The fix is minimal yet complete: storage now correctly returns multiples for name ambiguity, the rest of the stack (builders, agents, state, legacy, tests, docs) was updated consistently with plural messages and `num_matches` debug.
- Smart use of compat `"person"` field so existing smoke tests didn't need rewriting.
- Reuses `_run_mcp_query` path in some places? No, but the ping in health_check would now benefit if ever used on ambiguous names.
- Output.md is clear, includes exact before/after JSON, and honest follow-ups.
- Matches the original user complaint and the seed design decision (Kevin Zhang dups were intentional).

**Minor observations (non-blockers):**
- `response_not_found` message still uses singular "No core record found" (and "This lookup did not match anyone"). Could be made plural-friendly in a follow-up, but not required by the prompt and not a regression.
- `core_data_agent` docstring still mentions only "person" in one place (the implementation now correctly sets "persons"). Minor.
- Non-core row in the architecture table still says "core dict if person exists" — slightly stale but the main "found" row was updated.
- No new dedicated multi-match smoke test was added (per prompt guidance: "optional... Grok to classify"). The stub tests cover the single case; multi is exercised via the CLI smoke in verification.
- The legacy `evaluate_supervisor_turn` now supports multi, which is fine (even if only used in tests today).

**Workflow compliance:** Excellent. Claim, discovery (repro + seed history), implementation only in scope, smoke-only verification, clean artifacts, proper output.md with commands and follow-ups. No scope creep.

---

## Recommendation

**Accept / land the task.**

"Kevin Zhang" now correctly returns both people. The system handles ambiguous core names gracefully while keeping unique-name and ID behavior identical.

No immediate follow-up prompt required. The optional items in Cursor's output (dedicated multi test, future specialist disambiguation) can be queued later when prioritized.

**Project state:** Core identity resolution now properly supports the duplicate names that were intentionally kept in the 457-record seed. Query surface (CLI/MCP) transparently benefits.

(Review written after reading all artifacts + task prompt, inspecting full diffs, re-running smoke + manual queries for Kevin + unique + non-core cases, checking payload/state, and confirming scope via git.)
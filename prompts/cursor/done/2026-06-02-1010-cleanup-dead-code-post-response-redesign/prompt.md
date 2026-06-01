# Task: Clean Up Dead Code After PersonResponse Redesign

**Created:** 2026-06-02

**Objective:** Remove or clearly deprecate code that is no longer used or relevant after the minimalist `PersonResponse` redesign (task 1912) and the ingestion stubbing.

**References:**
- TODO item: "Clean up now-unused code (`DataRequest` if reintroduced, old status literals, redundant graph ingest nodes)."
- Current `src/models/state.py`
- Current `src/agents/supervisor.py`
- `src/graphs/core.py`

---

## Background

The minimalist response model change and ingestion stubbing left behind several pieces of dead or near-dead code:

- The old `DataRequest` model (was removed in an earlier pass but should be confirmed).
- Old `status` literal values and related handling in `PersonResponse`.
- Possibly unused fields or logic in `MyceliumGraphState`.
- Redundant wiring for enrich/validator nodes that are no longer reached for ingestion.
- Any lingering references to the old response shape in comments, docstrings, or tests.

## Scope

**In scope:**
- Identify and remove clearly dead code related to the old response model.
- Remove or comment out unused graph node wiring if it is truly unreachable.
- Clean up comments, docstrings, and type hints that reference removed concepts.
- Update or remove tests that only existed to support the old behavior.

**Out of scope:**
- Do not refactor `MyceliumGraphState` for cleanliness unless the code is genuinely unreachable and removal is trivial.
- Do not change behavior of the current (working) lookup paths.
- Do not redesign anything — this is pure cleanup.

---

## Step-by-Step Instructions

1. **Claim the task** by moving this file to `in-progress/`.

2. **Audit the codebase**
   - Search for references to the old `PersonResponse` fields (`status`, `person`, `data`, `data_request`, `deferred_attributes`, `errors`).
   - Search for `DataRequest`.
   - Search for old status values (`"found"`, `"data_request"`, `"specialist_required"`, `"ingested"`, `"validation_failed"`).
   - Review `src/graphs/core.py` for any ingest-related routing that is now dead.
   - Review `tests/` for tests that are now obsolete.

3. **Propose cleanup plan**
   In your `output.md`, list exactly what you plan to delete or modify, with justification.

4. **Perform the cleanup**
   - Remove dead code and models.
   - Clean up comments and docstrings.
   - Remove or mark obsolete tests.
   - Keep changes reviewable (small, well-described commits if possible).

5. **Verify**
   - Run the full test suite.
   - Run ruff + any type checking.
   - Manually verify that normal query flows still work.

6. **Deliver artifacts** per the standard workflow.

---

## Success Criteria

- [ ] All references to removed response concepts have been cleaned up from production code.
- [ ] No dead models (`DataRequest`, etc.) remain unless intentionally kept for a documented reason.
- [ ] Tests still pass and are not polluted with obsolete cases.
- [ ] The codebase is noticeably cleaner with no loss of current functionality.
- [ ] TODO.md is updated to mark this item complete.

---

**Keep this task narrow and focused on removal of dead weight.** If you discover larger refactoring opportunities, note them as follow-ups rather than implementing them.
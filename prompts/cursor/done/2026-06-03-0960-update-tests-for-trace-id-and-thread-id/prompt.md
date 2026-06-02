# Task: Update Tests for trace_id and thread_id in Responses

**Created:** 2026-06-03

**Objective:** Update existing tests and add new assertions so that the new `trace_id` and `thread_id` fields are verified in `PersonResponse` objects.

**References:**
- Previous tasks in the 09xx series
- `tests/test_core_graph.py`

---

## Scope (Strict)

**In scope:**
- Update relevant tests in `test_core_graph.py` (and any other test files) to check that `trace_id` and `thread_id` are present and correctly populated in responses.
- Add tests for both lookup and ingest paths where appropriate.
- Ensure test fixtures properly support passing `thread_id`.

**Out of scope:**
- Major new test infrastructure.
- Changes outside the test files.

---

## Step-by-Step Instructions

1. **Claim the task**

2. **Audit current tests**
   - Find all places where `run_query` is called and responses are asserted.
   - Identify which tests should now assert on the new fields.

3. **Update tests**
   - Add assertions that `thread_id` matches what was passed in (or the generated default).
   - Add assertions for `trace_id` (it may be `None` in some test environments; handle that gracefully or use the stubbed identity approach from previous tests).

4. **Add or extend tests**
   - Consider adding a simple test that verifies the fields flow through for both successful lookup and ingest.

5. **Verify**
   - `uv run pytest`
   - `uv run ruff check`

---

## Success Criteria

- [ ] Tests assert on the presence and correctness of `trace_id` and `thread_id` where appropriate.
- [ ] All tests pass.
- [ ] Ruff is clean.

---

**Keep this task focused on test updates.** This is the last code change before documentation.

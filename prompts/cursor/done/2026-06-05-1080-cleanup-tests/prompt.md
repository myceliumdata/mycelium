# Task: Remove or adapt all ingest-related tests

## Objective
Clean the test suite of tests that exercised the public ingest/add path (now removed). Update or delete the relevant test functions in `tests/test_core_graph.py` and `tests/test_supervisor_routing.py` (and any others) so that only query/lookup behavior remains. Keep test coverage for the query paths and the new core data agent (once wired).

## Constraints
- Do not leave failing tests.
- Preserve (and possibly expand) tests for pure query cases, non-core, not-found, thread_id propagation, etc.
- The `temp_storage` fixture and other test helpers can stay.
- After this task the test file should not import or construct anything with `provided_data` for public paths.

## Exact Steps
1. Edit `tests/test_core_graph.py`:
   - Delete or mark skipped: `test_ingest_new_person`, `test_ingest_validation_failure`, `test_run_query_echoes_thread_id_on_ingest`, and any asserts that check for "ingest_required" / "provided_data" messages.
   - Update `test_not_found_message_suggests_ingest` (if it exists) or similar to a plain not-found test.
   - Keep and verify the lookup, non-core, thread_id, and results-are-dicts tests.
2. Edit `tests/test_supervisor_routing.py`:
   - Remove or adapt any tests that exercised the ingest decision branches in routing.
   - Keep pure lookup delegation tests.
3. Run the test suite (`uv run pytest -q`) and ensure everything that remains passes.
4. If the new core_data_agent was introduced in a prior task, add or adapt at least one test that exercises it (optional but recommended if time).

## Required Output
- Diffs of the test files.
- Final `uv run pytest -q` output in the done/ summary.
- Notes about any tests that will need re-adding when ingest support returns later.

Claim via the standard next/ → in-progress/ move first.

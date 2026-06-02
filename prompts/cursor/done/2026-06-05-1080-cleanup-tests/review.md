# Review: 2026-06-05-1080-cleanup-tests

**Status:** Approved.

## What was done
- Confirmed that ingest tests were already removed in the 1000–1050 batch (no need to re-delete `test_ingest_new_person`, `test_ingest_validation_failure`, `test_run_query_echoes_thread_id_on_ingest`, or similar).
- Expanded query-only test coverage and added explicit checks for the new core_data flow:
  - In `tests/test_core_graph.py`: module docstring updated to "query-only public paths"; added `test_graph_invokes_supervisor_then_core_data` which does direct `build_core_graph()` + `ainvoke` and asserts audit_log contains "Supervisor" routing + "CoreDataAgent" lookup, plus response shape. Kept/verified all pure query tests (existing, missing, non-core attrs, plain-dicts, thread_id echo, default thread).
  - In `tests/test_supervisor_routing.py`: added `test_routing_non_core_attributes`, `test_supervisor_agent_routes_to_core_data` (asserts route="core_data", "response" not in supervisor result); updated not-found test with no-ingest-language asserts (`"ingest" not in ...`, `"provided_data" not in ...`).
  - In `tests/test_core_data_agent.py`: added `test_core_data_agent_non_core`.
- No changes needed to remove ingest branches from routing tests (already gone from prior tasks); kept the "pure lookup delegation tests" per prompt (even though `evaluate_supervisor_turn` is now test-only).
- Ran `uv run pytest -q` (22 passed) and `uv run ruff check tests`.
- Output.md documents the re-add list for when internal ingestion returns later.

## Code quality
- Tests now properly target the post-1070/1080 architecture: supervisor is thin (only route decision, no response), `core_data_agent` does the `CoreIdentity` lookup + response building + audit, graph test exercises the exact START-supervisor-core_data-END flow.
- Using `asyncio.run` on `ainvoke` in the graph test is appropriate and matches how the CLI/MCP sync bridge (`run_query`) works.
- Negative "ingest" / "provided_data" asserts in not-found test are good hygiene to prevent regression.
- Reuses the `_StubCoreIdentity` pattern consistently across routing and core_data tests.
- Matches prompt requirements exactly: deletions not re-done (already prior), added core_data coverage as "optional but recommended", verified full suite, noted future tests.
- 22 tests is a solid expansion after the removals.

## Verification
- From Cursor output: 22 passed, ruff clean.
- My runs: `uv run pytest -q` → 22 passed; `uv run ruff check src tests` → clean.
- Grep of `tests/` for `ingest|provided_data|enrich|validator|response_ingest` only hits the intended negative asserts in the not-found test.
- No stray imports of removed `person_prep`/`enrich`/`validator` agents in any test file.
- CLI smoke: `uv run mycelium query --person-key "Nichanan Kesonpat"` succeeds (exercises found path through supervisor + core_data); not-found case also works cleanly.
- MCP server imports cleanly (`from mycelium_mcp.server import query_person`) and is wired only to `run_query` (no ingest tool remains).
- Direct inspection of `test_core_graph.py:109`: the new test correctly constructs `MyceliumGraphState(query=...)` only, checks joined `audit_log` for both "Supervisor" and "CoreDataAgent".
- `test_supervisor_routing.py` still exercises the `evaluate_supervisor_turn` path (which builds responses), but the new `test_supervisor_agent_routes_to_core_data` specifically validates the thin live supervisor behavior used by the graph.
- Confirmed `tests/test_core_graph.py` has no remaining constructs using `provided_data`.

## Issues / Notes
- None blocking. The `evaluate_supervisor_turn` + `SupervisorDecision` tests in `test_supervisor_routing.py` are legacy/test-only now (the classification + response logic was moved/duplicated into `core_data._build_lookup_response` for the specialist agent). The 1080 prompt explicitly said "Keep pure lookup delegation tests" so leaving them is correct.
- Good that output.md precisely lists what must be re-added later: "Public ingest via `provided_data` on `PersonQuery`", "Graph enrich → validator loop", "`response_ingest_success` / `response_ingest_failure`", "MCP `submit_person_data` integration tests".
- No other test files required attention (earlier batches had removed `test_mcp.py` / `test_cli.py` ingest coverage).
- Matches the constraint: "After this task the test file should not import or construct anything with `provided_data` for public paths" — satisfied.

**Recommendation:** Approve. 1080 successfully completes the test-side of the public ingest removal + core_data_agent introduction. The test suite now only exercises and validates the query-only public surface with the proper specialist agent handoff.

**Follow-up:** In 1110 (final-cleanup-and-verification), consider whether to prune the now-test-only `evaluate_supervisor_turn` (and its SupervisorDecision) or leave as a living spec for the classification behavior that core_data_agent also implements. Also do the global remaining-reference sweep (tmp/, docs/, TODO.md) and the full CLI + MCP + graph smoke as specified in 1110. Task 1100 should ensure `__init__.py` and any init wiring is clean.

Reviewed by Grok.

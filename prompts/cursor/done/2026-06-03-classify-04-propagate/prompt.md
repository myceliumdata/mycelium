# Task: Classification Engine Phase 1 - Slice 04: Propagate classifications into core_data, responses, and full test isolation

**Read these first (mandatory):**
- `docs/plans/classification-engine-phase1.md` (the approved plan - focus on Step 4, "Propagation to 'the result' (PersonResponse)", the exact propagation code notes for core_data and responses, the test_core_graph fixture updates, the verification for full non-core, lightweight note)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`

**Objective**
Make the classification metadata visible in the PersonResponse (via debug) and the final graph state. Update core_data_agent to forward the classifications from incoming state into the payload. Update responses.py (debug_for_query or the builder calls) to include the classifications info in the debug string. Update the temp_storage fixture and non-core tests in test_core_graph.py to set MYCELIUM_CATEGORIES_PATH, reset the category tree, and assert the metadata appears for non-core requested attrs.

This completes the end-to-end for metadata in results for the current core_data path. Previous slice (03) made it appear in audit from supervisor; this makes it in the user-visible response.debug.

**Lightweight priority**
Follow the note: keep changes simple. Prioritize the propagation working cleanly.

**Constraints & Principles**
- Narrow scope (see box).
- Use patterns from approved plan and existing code ( **extra in debug_for_query, payload dicts, the fixture monkeypatch style from other MYCELIUM_*_PATH).
- Small reviewable changes.
- Smoke default; run targeted full for the non_core tests in this slice.
- Part of the small sequence (big monolithic prompt superseded).

**Context**
- After slice 03, supervisor injects "classifications" into state/audit for requested_attributes.
- core_data_agent and responses currently ignore it; the "still researching" path in core_data builds the response without the metadata in debug.
- The approved plan specifies exactly where to copy classifications into payload in _run_core_data_lookup, and how to thread into debug_for_query or the response_non_core etc calls.
- The test_core_graph.py temp_storage fixture already does resets and env for db/seed/checkpoint; we add the categories one + reset_category_tree.
- After this, full manual non-core queries will have the metadata in .debug, and the full non_core tests will assert it.
- Still no change to routing or specialist creation.

See approved plan for the precise code locations and the "Verify: ... full non-core graph test" commands.

**Exact Steps (perform in order)**
1. **Claim first**: Move this to in-progress/ per WORKFLOW. Document.

2. **Discovery**:
   - Read the approved plan Step 4 section and propagation notes.
   - Read current `src/agents/core_data.py` (_run_core_data_lookup, _build_lookup_response, payload construction).
   - Read `src/agents/responses.py` (debug_for_query, the response_* builders, how non_core_requested is passed in extra).
   - Read `tests/test_core_graph.py` (the temp_storage fixture, the test_query_non_core_attributes test).
   - Baseline: `uv run pytest -m smoke -q` and the full non-core key test if possible.
   - Repro a non-core query and note that debug does not yet mention classifications.

3. **Update core_data.py**:
   - In core_data_agent or _run_core_data_lookup (after current = _coerce(state)), capture classifications = getattr(current, "classifications", []) or current.classifications if present.
   - Include "classifications": classifications in the returned payload dict (so it ends up in final graph state after core_data node).
   - Pass it down to _build_lookup_response if needed, or capture before calling the response builders.
   - Keep the non_core decision logic unchanged.

4. **Update responses.py**:
   - Enhance debug_for_query to handle non-str values gracefully (e.g. for lists/dicts: use repr or json.dumps with default=str, or just str(value)).
   - Or, in the calls inside response_non_core (and found/not_found for consistency), pass classifications=... (a compact str or the list) via the **extra.
   - Update the non_core builder to include e.g. classifications=... in the debug if provided.
   - The goal per approved: response.debug now contains the classification metadata for non-core attrs.

5. **Update tests/test_core_graph.py**:
   - In temp_storage fixture: import reset_category_tree, call it in setup and teardown.
   - Add monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(tmp_path / "categories.json"))
   - In the non-core test (test_query_non_core_attributes or equivalent), after the query, assert that "classifications" or the category info appears in response.debug (or num_matches etc. still work).
   - Optionally inspect the graph result for state.classifications if easy in the test.

6. **Verification for this slice**:
   - `uv run pytest -m smoke -q`
   - `uv run pytest -m full -q -k "non_core or query_non_core"` (the targeted full ones must pass and show evidence of classifications in debug or state).
   - Manual: `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email`
     - Now response.debug should include the classifications info (in addition to the audit from previous slice).
   - Same for unknown attr and multi (Kevin Zhang + attr).
   - Confirm git changes limited to the 3 files in scope for this slice.
   - Confirm the engine is still using the seed (no breakage to classify).

7. **Output**:
   - done/2026-06-03-classify-04-propagate/output.md with summary, decisions (e.g. "made debug_for_query tolerant of lists by str/repr; passed via extra in non_core builder"), full outputs of the commands above, diffs for *this slice only*, scope confirmation.
   - prompt.md copy.
   - Remove only your claim from in-progress/.

**Scope Boundaries (Strict)**
You may only modify:
- `src/agents/core_data.py`
- `src/agents/responses.py`
- `tests/test_core_graph.py`

**Out of Scope (Do Not Touch)**
- classification/ , state.py, supervisor.py (previous slices).
- mcp, graphs, main, storage, other docs/tests, the superseded prompt, approved plan.
- Do not change routing or add new fields to PersonResponse.

Stop and follow-up prompt if you need something outside.

**Test Execution Policy**
- smoke -q
- For this slice, run the full marker targeted tests as shown (per approved plan and WORKFLOW: when touching full tests, run them immediately).
- Mark any new tests appropriately.

**Output Location**
`prompts/cursor/done/2026-06-03-classify-04-propagate/output.md` etc. per WORKFLOW.

Claim, do the narrow propagation work, verify the slice, deliver artifacts.

After review of this slice (we will re-run the full non-core key tests + manuals + check that metadata is now in debug), we will prepare slice 05 (refresh).

Keep it small and per the approved plan's propagation notes. Good luck.
# Task: Classification Engine Phase 1 - Slice 06: Polish, docs, ruff, and full end-to-end verification matrix

**Read these first (mandatory):**
- `docs/plans/classification-engine-phase1.md` (the approved plan - this slice executes Step 6 + 7 and the entire "Verification (End-to-End + Regression)" section at the end of the approved plan, including all automated, manual hot-path, test isolation & cache, off-path LLM refresh, no hot-path LLM guarantee grep, observability, lint, and success criteria)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md` (the small doc update location: under "Derivative / Non-Core Data" or supervisor section, the 1-2 sentence mention of Phase 1 Classification Engine)

**Objective**
Polish the implementation (ruff on touched files, optional small atomic save if the diff is tiny per lightweight, optional __init__ export), add the small doc update in architecture.md, run the *full* verification matrix from the approved plan (smoke + full targeted + every manual hot-path command, Kevin Zhang + attr, MCP path, reseed on delete json, off-path refresh, all greps, etc.), ensure everything is clean and the "No LLM on hot path" + "classifications in audit/debug/state" guarantees hold.

This is the final slice. After this, Phase 1 per the approved plan is complete, having been built and reviewed in small increments.

**Lightweight priority**
Any polish (e.g. making _save atomic with tempfile) only if it fits as a small diff at the end. Do not force large changes now.

**Constraints & Principles**
- Scope: the remaining polish items + the full verify run (no new big logic).
- All prior slices' behavior must be preserved and enhanced only with the metadata.
- Use the exact verification commands and success criteria from the approved plan.
- Small final increment.

**Context**
- Slices 01-05 have delivered: seed+package, engine (classify + unknown + simple save), supervisor injection + state + audit, propagation to payload + debug + fixture, refresh (off-path, mocked in tests).
- Now run the complete matrix the approved plan specifies at the end, plus the small polish and the 1-2 sentence doc update.
- The big prompt is long superseded.
- This slice will touch multiple files for polish/verify, but the actual code changes should be tiny (ruff fixes, one sentence in docs, perhaps the atomic if small).

See the full "Verification (End-to-End + Regression)" and "Success criteria for Phase 1" in the approved plan.

**Exact Steps (perform in order)**
1. **Claim**: Move to in-progress/. Document.

2. **Discovery / baseline**:
   - Re-read the verification section and success criteria in the approved plan.
   - Re-read the small doc update suggestion in Step 6.
   - Run baseline smoke and a couple manual queries to have before state.
   - Confirm all previous slices are in (e.g. classifications in audit from 03, in debug from 04, refresh in engine from 05).

3. **Polish (tiny changes only)**:
   - Run `uv run ruff check src/agents/classification src/agents/supervisor.py src/agents/core_data.py src/models/state.py tests/test_supervisor_routing.py tests/test_core_graph.py tests/conftest.py` and fix any issues (small auto or manual fixes).
   - Optional: if the current _save is still plain write_text and you can make the atomic tempfile+replace version with a *very small* diff, do it now (per lightweight "only if it fits small changes"). Otherwise leave simple.
   - Optional: tiny addition to src/agents/__init__.py to re-export the classification symbols (only if it is a one-liner and useful; low priority per approved plan).
   - Small doc update in `docs/architecture.md`: add 1-2 sentences in the appropriate place (e.g. under "Derivative / Non-Core Data" or the supervisor paragraph) saying something like: "Phase 1 adds a Classification Engine (fast cached lookup in src/agents/classification/ backed by data/categories.json) that the supervisor uses for non-core requested_attributes. It injects category/assigned_agent/description/confidence metadata into audit_log, state.classifications, and response.debug. LLM is used only off the hot path for occasional tree evolution (see docs/plans/classification-engine-phase1.md)."

4. **Run the full verification matrix (from approved plan - execute every command)**:
   - Automated: `uv run pytest -m smoke -q`
   - `uv run pytest -m full -q -k "non_core or query_non_core or supervisor_agent or classify"`
   - `uv run ruff check` on the listed files.
   - Manual hot-path (zero LLM):
     - Core only query.
     - Known non-core (email, spouse) - check audit has classified line, debug has classifications.
     - Unknown attr.
     - Ambiguous name + attr (Kevin Zhang + x_handle) - 2 results + metadata.
     - MCP path equivalent python -c query_person with attrs.
   - Test isolation & cache:
     - MYCELIUM_CATEGORIES_PATH override + reset + classify.
     - Delete (or mv aside) data/categories.json, run a classify/query with attr, confirm it still works via the embedded seed (may rewrite the file).
     - Restore the committed json.
   - Off-path LLM refresh:
     - The python -c refresh example (with key if available; otherwise the no-op/early paths).
     - Confirm after refresh a classify sees new mapping.
   - No hot-path LLM guarantee:
     - The exact `git grep -n "ChatOpenAI|refresh_from_llm|...` command on the listed src/ paths.
     - Must have zero hits outside classification/engine.py (and only the method inside).
   - Observability: classifications visible in state (if you can inspect in a test or manual).
   - Lint + hygiene: ruff clean, no changes outside the overall approved structure list, json roundtrips.
   - Capture *all* output.

5. **Final manual matrix** (repeat the key ones from approved plan):
   - All the ones listed under "Manual hot-path...", "MCP path", "Cache: delete...", etc.
   - Confirm success criteria: fast classify, unknown safe with 0 conf, persistent json, LLM never on hot path, supervisor injects with minimal change, tests + matrix green, ready for Phase 2.

6. **Output artifacts**:
   - `prompts/cursor/done/2026-06-03-classify-06-polish-full/output.md`:
     - Summary of the final polish + doc sentence + that the full matrix was run.
     - *All* the command outputs from the verification (paste the full logs).
     - Diffs for the polish changes in this slice (should be very small).
     - Confirmation that every item in the approved plan's success criteria and verification is satisfied.
     - Note that all prior slices were reviewed incrementally.
   - prompt.md copy.
   - Remove only your claim from in-progress/.

**Scope Boundaries (Strict)**
You may modify in this final polish slice:
- The files touched for ruff fixes / small atomic if done / optional __init__ export (but keep minimal).
- `docs/architecture.md` (the 1-2 sentence addition only).
- Running verification commands (which may touch temp files or the json via reseed test).

Primarily the changes should be the doc sentence and any ruff cleanups. Do not re-implement logic from prior slices.

**Out of Scope**
- Big changes, new features, touching the superseded prompt, editing the approved plan, large refactors.
- Anything that would violate the "small" nature of this final slice.

If something big is needed: stop and follow-up prompt.

**Test Execution Policy**
- Run smoke and the full targeted as specified in the matrix.
- This slice runs the "full" verification because it is the final one.

**Output per WORKFLOW**
done/2026-06-03-classify-06-polish-full/...

Claim, do the tiny polish + the *complete* verification run from the approved plan, document everything in output.md, deliver.

After this, we will do the final review of the whole series (re-run key parts of the matrix), add review.md to this last done/, and then commit the completed Phase 1 (small slices make the commit history clean).

This completes the approved plan via small, reviewed increments. Execute cleanly. Good luck.
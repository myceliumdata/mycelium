# Task: Reprocess - Redesign Slice 1520: unify-responses (from 2026-06-07 redesign)

**Read these first (mandatory):**
- `prompts/resets/2026-06-07_redesign_reset.md` (FULL context, the description of this slice in the 'Completed & Reviewed Slices' section, the target model from user's proposed new model, all slice history, seed generation process, overall redesign. This is the source of truth for what this slice must achieve. Do not summarize or lose details.)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`
- `prompts/system/CORE_PROMPT.md`

**Objective**
Implement exactly the 1520-unify-responses slice as described for **1520-unify-responses** (reviewed) in the redesign_reset.md.

From the reset: responses.py: _build_identity_results (supports base_records), updated messages (no "core record", "Found record for...", "No record found for...", "We're still researching... (via ...)"). response_found/non_core accept base_records. Updated core_data.py call sites minimally, test asserts for new strings (including extra smoke touch to test_supervisor_routing.py noted transparently).

This is a reprocess of a previously executed and reviewed Cursor task whose output (done/ dir) was destroyed in the backout. Produce the changes and the full output.md in a *new* done/ dir using this prompt's name (2026-06-09-1520-unify-responses-reprocess) to avoid overwriting any previous version. Follow the same scope, verification, and output format as the original. Deliver only prompt.md (copy of this) and output.md (summary of changes, git diff --stat, full verification outputs, scope confirmation, "Ready for next slice"). Grok will perform the substantive review and add review.md after delivery.

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. ... " (see full in redesign_reset.md)

**Constraints & Principles**
- Strictly follow the claiming process in WORKFLOW.md exactly (move this file to in-progress/ with subdir before any work).
- Reference the redesign_reset.md for full previous prompt details, scope, verification, and the overall target model (seed JSON as origin, supervisor passes full context (seed + union of specialist data) to all relevant specialists, specialist data wins, 3 scenarios, no core specialist, etc.).
- Only implement what was in the 1520 slice; do not do later slices' work.
- Run only smoke tests + the specific verifs from the reset for this slice.
- Deliver to done/2026-06-09-1520-unify-responses-reprocess/ containing prompt.md (copy of this) and output.md only. Do not create review.md — Grok will review and add it after.

**Context**
The full history, what the original prompt contained, what was delivered, the verifications that passed, and the state before/after this slice are all in prompts/resets/2026-06-07_redesign_reset.md under the 1520 section, the "Current Project State Snapshot", the user's proposed new model, and related sections on context passing and unified messages (no more "core record" language).

See the redesign_reset for the exact target (unified response builders that support base_records from seed/specialists, updated messages for the redesign model).

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, select this, **immediately move** it to `prompts/cursor/in-progress/2026-06-09-1520-unify-responses-reprocess/prompt.md` (create the subdir if needed). Only then begin work. Document the move and timestamp in your output.md. Never work on a file still in next/.

2. **Discovery (read-only)**: 
   - Read the 1520 section and surrounding context in the redesign_reset.md (including the overall target model, unified messages, base_records support).
   - Read current `src/agents/responses.py` (the builders: response_found, response_non_core, response_not_found, _make_response, debug_for_query, _build_identity_results if present).
   - Read `src/agents/core_data.py` for call sites.
   - Read relevant tests (test_supervisor_routing.py etc.) that assert on message strings.
   - Run `git status`, `ls src/agents/`, etc. to confirm current state.
   - Run `uv run pytest -m smoke -q` as baseline.

3. **Implement the changes for this slice exactly**:
   - In `src/agents/responses.py`: Introduce or update `_build_identity_results` (supports base_records from seed or specialists).
   - Update the message strings in the builders to the new unified language (no "core record", "Found record for...", "No record found for...", "We're still researching... (via ...)").
   - Make `response_found` and `response_non_core` accept `base_records` parameter.
   - Update call sites in `core_data.py` (minimally) to pass the new args.
   - Update test asserts in `test_supervisor_routing.py` (and any others) for the new strings (noted transparently in the original).
   - Ensure the changes support the redesign (messages will later incorporate contributions from specialists and "via <specialist>" labels).

4. **Verification**: Run exactly the smoke + any full tests + manual checks listed/appropriate for 1520 in the redesign_reset.md (tests green, new message strings appear correctly, base_records support, no breakage to existing paths). Include the extra smoke touch to test_supervisor_routing.py.

5. **Output artifacts**: Create the done/ dir with new name 2026-06-09-1520-unify-responses-reprocess/ containing:
   - prompt.md (copy of this)
   - output.md with summary of what was done, git diff --stat, full output of all verification commands, confirmation scope respected, any open questions, "Ready for next slice".

6. Remove only the file you claimed from `in-progress/`.

**Scope Boundaries (Strict)**
Only the changes for this slice as described in the redesign_reset.md 1520 section (responses.py _build_identity_results + updated messages + base_records support on found/non_core; minimal core_data.py call site updates; test assert updates for new strings in test_supervisor_routing.py and similar). Do not touch state model, supervisor logic, graph, eliminate core, or any later slice work.

**Test Execution Policy**
Default to smoke tests. Use full tests only for the specific ones relevant to responses (as in the original for this slice). Document the category.

**Required Output Location & Artifacts**
prompts/cursor/done/2026-06-09-1520-unify-responses-reprocess/ (use the reprocess name so that when moved to done/ it does not overwrite any previous version of this slice). Deliver prompt.md and output.md only.

Follow WORKFLOW.md claiming exactly before doing any implementation work. Reference the full redesign context in the reset file (user's exact model, unified messages for the new context model, etc.). Make the implementation and artifacts match what was reviewed and approved originally for 1520 as documented in the redesign_reset.md.

This reprocess restores the 1520 Cursor task (unify responses for the seed-data-context redesign) whose output was destroyed. Use the redesign_reset.md for the full original details and to make the changes match the intended result.

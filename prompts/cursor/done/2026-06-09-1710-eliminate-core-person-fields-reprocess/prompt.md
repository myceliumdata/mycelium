# Task: Reprocess - Redesign Slice 1710: eliminate-core-person-fields (from 2026-06-07 redesign)

**Read these first (mandatory):**
- `prompts/resets/2026-06-07_redesign_reset.md` (FULL context, original prompt details, what Cursor delivered in output, verification matrix, the target model from user's words, all slice history, seed generation process. This is the source of truth for what this slice must achieve. Do not summarize or lose details.)
- `docs/plans/seed-data-context-architecture.md` (the plan; if missing or incomplete, the full plan description is in the redesign_reset.md under "Plan: Evolving Mycelium...")
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`
- `prompts/system/CORE_PROMPT.md`

**Objective**
Re-execute exactly the 1710-eliminate-core-person-fields slice as described in the 'Completed & Reviewed Slices' section of the redesign_reset.md for **1710-eliminate-core-person-fields** (sibling to 1700).

From the reset:
- **1710-eliminate-core-person-fields** (sibling to 1700): Removes CORE_PERSON_FIELDS / non_core_attributes / the privileged core notion entirely so name/employer queries properly surface specialist status. Updates assemble + template so *any* requested attr (incl. name) goes through specialist status/contribution path. Requesting "name" will now show proper "not currently available... (via contact_specialist)" (or value) while still returning identity record.

This is a reprocess of a previously executed and reviewed Cursor task whose output was destroyed. Follow the same scope, verification, and output format as the original. Use the redesign_reset.md for the exact original prompt text, decisions, and what "output.md" and verification should contain. Produce equivalent changes to the code and the full output.md artifacts (Grok will add review.md) in a new done/ dir with this prompt's name (to avoid overwriting previous version).

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. ... " (see full in redesign_reset.md)

**Extra Guidance from Paul**
(see the full redesign context in the reset file)

**Constraints & Principles**
- Strictly follow the claiming process in WORKFLOW.md exactly (move this file to in-progress/ with subdir before any work).
- Reference the redesign_reset.md for full previous prompt, scope, verification commands, and the overall target model (seed JSON, no core specialist, context passing, etc.).
- Only implement what was in the 1710 slice; do not do later slices' work.
- Run only smoke tests + the specific verifs from the reset for this slice.
- When delivering, put into done/2026-06-09-1710-eliminate-core-person-fields-reprocess/ (new name) with prompt.md (copy of this), output.md.
- Deliver only prompt.md and output.md. Do not create review.md — Grok will review the work and add the review.md after.

**Context**
The full history, what the original prompt contained, what was delivered, the verifications that passed, and the state before/after this slice are all in prompts/resets/2026-06-07_redesign_reset.md under the 1710 section and the "Current Project State Snapshot".

See the approved detailed plan and the redesign_reset for exact seed content, file changes, etc.

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Move this file to `prompts/cursor/in-progress/2026-06-09-1710-eliminate-core-person-fields-reprocess/prompt.md`. Document in your output.md.
2. **Discovery (read-only)**: Read the 1710 section (and related 1700/1720 notes) in redesign_reset.md , current responses.py (assemble), specialist_agent.py.j2, tests, etc.
3. **Implement the changes for this slice exactly**: Perform the actions described for 1710 in the reset: Removes CORE_PERSON_FIELDS / non_core_attributes / the privileged core notion entirely so name/employer queries properly surface specialist status. Updates assemble + template so *any* requested attr (incl. name) goes through specialist status/contribution path. Requesting "name" will now show proper "not currently available... (via contact_specialist)" (or value) while still returning identity record.
4. **Verification**: Run the tests green as listed for 1710 in the reset. Update any affected tests/fixtures as in original.
5. **Output artifacts**: Create the done/ dir with new name 2026-06-09-1710-eliminate-core-person-fields-reprocess/ containing:
   - prompt.md (this file)
   - output.md with summary, git diff --stat, full verification outputs, scope confirmation, "Ready for next slice: 2026-06-09-1720-eliminate-id-from-seed-transform-reprocess.md".
   (Grok will add review.md after reviewing the delivered prompt.md + output.md.)
6. Remove only your claim from in-progress/.

**Scope Boundaries**
Follow exactly the scope from the original 1710 as described in the redesign_reset.md 1710 section. Do not touch things for later slices (e.g. do not implement the seed id transform / prepare_seed.py changes yet).

**Test Execution Policy**
Default smoke, plus the specific for this slice.

**Required Output Location & Artifacts**
prompts/cursor/done/2026-06-09-1710-eliminate-core-person-fields-reprocess/ (use the reprocess name so it does not overwrite any previous version in done/).

Follow WORKFLOW.md claiming exactly.

This reprocess is to restore the processed Cursor task whose output was destroyed in a previous backout. Make the implementation and artifacts match what was reviewed and approved in the original 1710 as documented in the redesign_reset.md.

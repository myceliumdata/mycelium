# Task: Reprocess - Redesign Slice 1720: eliminate-id-from-seed-transform (from 2026-06-07 redesign)

**Read these first (mandatory):**
- `prompts/resets/2026-06-07_redesign_reset.md` (FULL context, original prompt details, what Cursor delivered in output, verification matrix, the target model from user's words, all slice history, seed generation process. This is the source of truth for what this slice must achieve. Do not summarize or lose details.)
- `docs/plans/seed-data-context-architecture.md` (the plan; if missing or incomplete, the full plan description is in the redesign_reset.md under "Plan: Evolving Mycelium...")
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`
- `prompts/system/CORE_PROMPT.md`

**Objective**
Re-execute exactly the 1720-eliminate-id-from-seed-transform slice as described in the redesign_reset.md under the "The 1720 Prompt" section (created at user's request; note that 1720 was not yet executed at the time of the reset).

From the reset:
- **1720-eliminate-id-from-seed-transform**: (detailed in "The 1720 Prompt" section). Creates `data/prepare_seed.py` (the reusable transform file): reads seed_crm.json, strips "id" from each person (output only name + employer), writes clean seed.json. Regenerates data/seed.json via the script (will have no "id" keys). Updates src/agents/seed.py (enrichment: no longer sets seed_id from static "id"; person_id always assigned). Updates src/agents/supervisor.py ( _identity_records_from_seed and _persons_from_seed now set "id" to the person_id UUID; comments reference slice). Updates test fixture in test_core_graph.py (inline seed creation omits "id"; light UUID assert). Updates docs/architecture.md (seed.json now only name+employer; results "id" is the UUID). Verification: run prepare, inspect seed.json has no "id", manual queries (single + name attr) show results "id" is UUID (matches internal), multi-result has distinct UUIDs, smoke/full green, ruff, git-stat only scoped, grep no more "id" creation in transform path. Full context references the user's recent query with --attributes name (got old "person-0001" + full record incl. unrequested employer), the need for UUID in results, the 1700/1710 siblings, RESTART_PROMPT_FOR_PLAN.md, how seed generation works, reset policy (user replaces seed.json manually).

This is a reprocess of a previously executed and reviewed Cursor task whose output was destroyed. Follow the same scope, verification, and output format as the original. Use the redesign_reset.md for the exact original prompt text, decisions, and what "output.md" and verification should contain. Produce equivalent changes to the code and the full output.md artifacts (Grok will add review.md) in a new done/ dir with this prompt's name (to avoid overwriting previous version).

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. ... " (see full in redesign_reset.md)

**Extra Guidance from Paul**
(see the full redesign context in the reset file)

**Constraints & Principles**
- Strictly follow the claiming process in WORKFLOW.md exactly (move this file to in-progress/ with subdir before any work).
- Reference the redesign_reset.md for full previous prompt, scope, verification commands, and the overall target model (seed JSON, no core specialist, context passing, etc.).
- Only implement what was in the 1720 slice; do not do later slices' work.
- Run only smoke tests + the specific verifs from the reset for this slice.
- When delivering, put into done/2026-06-09-1720-eliminate-id-from-seed-transform-reprocess/ (new name) with prompt.md (copy of this), output.md.
- Deliver only prompt.md and output.md. Do not create review.md — Grok will review the work and add the review.md after.

**Context**
The full history, what the original prompt contained, what was delivered, the verifications that passed, and the state before/after this slice are all in prompts/resets/2026-06-07_redesign_reset.md under the 1720 section (and "The 1720 Prompt" + "How seed.json Is Generated") and the "Current Project State Snapshot".

See the approved detailed plan and the redesign_reset for exact seed content, file changes, etc.

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Move this file to `prompts/cursor/in-progress/2026-06-09-1720-eliminate-id-from-seed-transform-reprocess/prompt.md`. Document in your output.md.
2. **Discovery (read-only)**: Read the 1720 section ("The 1720 Prompt", "How seed.json Is Generated", related 1700/1710 notes) in redesign_reset.md , and the current data/ (seed_crm.json, seed.json), src/agents/seed.py, supervisor.py, test_core_graph.py, docs/architecture.md, etc. Also note the recent user query example with --attributes name.
3. **Implement the changes for this slice exactly**: Perform the actions described for 1720 in the reset (detailed in "The 1720 Prompt" section): Creates `data/prepare_seed.py` (the reusable transform file): reads seed_crm.json, strips "id" from each person (output only name + employer), writes clean seed.json. Regenerates data/seed.json via the script (will have no "id" keys). Updates src/agents/seed.py (enrichment: no longer sets seed_id from static "id"; person_id always assigned). Updates src/agents/supervisor.py ( _identity_records_from_seed and _persons_from_seed now set "id" to the person_id UUID; comments reference slice). Updates test fixture in test_core_graph.py (inline seed creation omits "id"; light UUID assert). Updates docs/architecture.md (seed.json now only name+employer; results "id" is the UUID). Verification: run prepare, inspect seed.json has no "id", manual queries (single + name attr) show results "id" is UUID (matches internal), multi-result has distinct UUIDs, smoke/full green, ruff, git-stat only scoped, grep no more "id" creation in transform path. Full context references the user's recent query with --attributes name..., the 1700/1710 siblings, etc.
4. **Verification**: Run the tests green as listed for 1720 in the reset. Update any affected tests/fixtures as in original.
5. **Output artifacts**: Create the done/ dir with new name 2026-06-09-1720-eliminate-id-from-seed-transform-reprocess/ containing:
   - prompt.md (this file)
   - output.md with summary, git diff --stat, full verification outputs, scope confirmation, "Ready for next slice (all redesign slices through 1720).".
   (Grok will add review.md after reviewing the delivered prompt.md + output.md.)
6. Remove only your claim from in-progress/.

**Scope Boundaries**
Follow exactly the scope from the original 1720 as described in the redesign_reset.md 1720 section ("The 1720 Prompt"). Do not touch things outside the listed changes (e.g. do not perform additional redesign work beyond the seed transform, UUID exposure in results, and related updates).

**Test Execution Policy**
Default smoke, plus the specific for this slice.

**Required Output Location & Artifacts**
prompts/cursor/done/2026-06-09-1720-eliminate-id-from-seed-transform-reprocess/ (use the reprocess name so it does not overwrite any previous version in done/).

Follow WORKFLOW.md claiming exactly.

This reprocess is to restore the processed Cursor task whose output was destroyed in a previous backout. Make the implementation and artifacts match what was described for the 1720 prompt in the redesign_reset.md (under "The 1720 Prompt" section).

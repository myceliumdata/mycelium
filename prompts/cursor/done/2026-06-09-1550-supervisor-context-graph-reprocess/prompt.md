# Task: Reprocess - Redesign Slice 1550: supervisor-context-graph (from 2026-06-07 redesign)

**Read these first (mandatory):**
- `prompts/resets/2026-06-07_redesign_reset.md` (FULL context, original prompt details, what Cursor delivered in output, verification matrix, the target model from user's words, all slice history, seed generation process. This is the source of truth for what this slice must achieve. Do not summarize or lose details.)
- `docs/plans/seed-data-context-architecture.md` (the plan; if missing or incomplete, the full plan description is in the redesign_reset.md under "Plan: Evolving Mycelium...")
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`
- `prompts/system/CORE_PROMPT.md`

**Objective**
Re-execute exactly the 1550-supervisor-context-graph slice as described in the 'Completed & Reviewed Slices' section of the redesign_reset.md for **1550-supervisor-context-graph** (reviewed).

From the reset:
- **1550-supervisor-context-graph** (reviewed): New src/agents/context.py (ContextBuilder.build_full_context using registry + SpecialistStorage pulls, TODO for peer retrieval). supervisor.py: planning only (collects *all* specialists_to_invoke via _collect_..., puts in context._meta, enriches matched_persons/context/current_person_id; always route=None). dispatch.py: build_context_node, invoke_specialists_node (sequential, enriches with context/person_id/target_fields, collects contributions), assemble_response_node (merges using contributions + pending logic in messages; legacy alias). graphs/core.py: new nodes + conditional routing per choice C (if specialists_planned -> build_context else direct assemble; edges for fan-in). Tests/fixtures updated. Manual CLI queries (name-only + multi-attr) exercise full flow (plans, builds context, invokes multiple, assembles with "via ..." + contributions in debug). Smoke + full green. No core_data left.

This is a reprocess of a previously executed and reviewed Cursor task whose output was destroyed. Follow the same scope, verification, and output format as the original. Use the redesign_reset.md for the exact original prompt text, decisions, and what "output.md" and verification should contain. Produce equivalent changes to the code and the full output.md artifacts (Grok will add review.md) in a new done/ dir with this prompt's name (to avoid overwriting previous version).

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. ... " (see full in redesign_reset.md)

**Extra Guidance from Paul**
(see the full redesign context in the reset file)

**Constraints & Principles**
- Strictly follow the claiming process in WORKFLOW.md exactly (move this file to in-progress/ with subdir before any work).
- Reference the redesign_reset.md for full previous prompt, scope, verification commands, and the overall target model (seed JSON, no core specialist, context passing, etc.).
- Only implement what was in the 1550 slice; do not do later slices' work.
- Run only smoke tests + the specific verifs from the reset for this slice.
- When delivering, put into done/2026-06-09-1550-supervisor-context-graph-reprocess/ (new name) with prompt.md (copy of this), output.md.
- Deliver only prompt.md and output.md. Do not create review.md — Grok will review the work and add the review.md after.

**Context**
The full history, what the original prompt contained, what was delivered, the verifications that passed, and the state before/after this slice are all in prompts/resets/2026-06-07_redesign_reset.md under the 1550 section and the "Current Project State Snapshot".

See the approved detailed plan and the redesign_reset for exact seed content, file changes, etc.

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Move this file to `prompts/cursor/in-progress/2026-06-09-1550-supervisor-context-graph-reprocess/prompt.md`. Document in your output.md.
2. **Discovery (read-only)**: Read the 1550 section in redesign_reset.md , current context.py (new), supervisor.py, dispatch.py, graphs/core.py, tests/fixtures, etc.
3. **Implement the changes for this slice exactly**: Perform the actions described for 1550 in the reset: New src/agents/context.py (ContextBuilder.build_full_context using registry + SpecialistStorage pulls, TODO for peer retrieval). supervisor.py: planning only (collects *all* specialists_to_invoke via _collect_..., puts in context._meta, enriches matched_persons/context/current_person_id; always route=None). dispatch.py: build_context_node, invoke_specialists_node (sequential, enriches with context/person_id/target_fields, collects contributions), assemble_response_node (merges using contributions + pending logic in messages; legacy alias). graphs/core.py: new nodes + conditional routing per choice C (if specialists_planned -> build_context else direct assemble; edges for fan-in). Tests/fixtures updated. Manual CLI queries (name-only + multi-attr) exercise full flow (plans, builds context, invokes multiple, assembles with "via ..." + contributions in debug). Smoke + full green. No core_data left.
4. **Verification**: Run the tests green as listed for 1550 in the reset. Update any affected tests/fixtures as in original.
5. **Output artifacts**: Create the done/ dir with new name 2026-06-09-1550-supervisor-context-graph-reprocess/ containing:
   - prompt.md (this file)
   - output.md with summary, git diff --stat, full verification outputs, scope confirmation, "Ready for next slice: 2026-06-09-1600-integration-tests-reset-docs-regen-reprocess.md".
   (Grok will add review.md after reviewing the delivered prompt.md + output.md.)
6. Remove only your claim from in-progress/.

**Scope Boundaries**
Follow exactly the scope from the original 1550 as described in the redesign_reset.md 1550 section. Do not touch things for later slices (e.g. do not implement integration tests reset or later slices yet).

**Test Execution Policy**
Default smoke, plus the specific for this slice.

**Required Output Location & Artifacts**
prompts/cursor/done/2026-06-09-1550-supervisor-context-graph-reprocess/ (use the reprocess name so it does not overwrite any previous version in done/).

Follow WORKFLOW.md claiming exactly.

This reprocess is to restore the processed Cursor task whose output was destroyed in a previous backout. Make the implementation and artifacts match what was reviewed and approved in the original 1550 as documented in the redesign_reset.md.

# Cursor Task: Clean up derivative dataset references in models

**Objective**  
Begin aligning the data models with the current Phase 1 direction by removing or significantly simplifying concepts around pre-defined "derivative datasets".

**Background**  
See `docs/phase-1-direction.md`, especially the sections on:
- Core Person model being strictly minimal
- No pre-definition of derivative datasets or attributes
- The supervisor acting as a coordinator rather than creating or managing derivative data structures

Currently, `src/models/state.py` still contains `DerivativeDatasetRef`, certain `PersonResponse` statuses (`derivative_pending`), and related helpers that assume a formal derivative dataset system. This is now out of alignment.

**Instructions**

1. **Before doing any work**, follow the discovery and claiming process defined in `prompts/WORKFLOW.md` (also reinforced by the Cursor rule in `.cursor/rules/04-cursor-workflow.mdc`):
   - Look for the oldest file in `prompts/next/` (sorted alphabetically by filename).
   - Move that file into `prompts/in-progress/`.
   
   This must be done even if Paul directly tells you the filename of this prompt. The claiming step is mandatory.

2. Perform the following:
   - Audit `src/models/state.py` for all derivative dataset related constructs (`DerivativeDatasetRef`, related statuses in `PersonResponse`, `attributes_requiring_derivative`, etc.).
   - Propose a minimal, clean set of changes that removes the assumption of pre-defined derivative datasets.
   - Implement the changes (or a first safe increment of them).
   - Update any obvious call sites in the rest of the codebase if they are trivial and low-risk.
   - Update `TODO.md` to reflect progress on the catch-up items.

3. **Output Requirements**

   Create the directory:
   `prompts/done/2025-06-01-1700-clean-derivative-references/`

   Inside it, produce at minimum:

   - `prompt.md` — Copy of this original prompt
   - `output.md` — A structured summary containing:
     - What you changed and why
     - Any remaining derivative-related concepts you left in place (and justification)
     - Files modified
     - Open questions or areas that need follow-up prompts
     - Whether `TODO.md` was updated
   - `review-notes.md` (optional) — Any thoughts you want to surface for Grok and Paul

4. Make clean, reviewable git commits. Use good commit messages that reference this task.

5. Do **not** attempt large refactors of the supervisor or storage in this task unless they are trivial side effects. Keep the scope focused on the models.

**Constraints**
- Stay aligned with `docs/phase-1-direction.md`.
- Prefer simplification and deletion over adding new abstractions.
- Keep changes incremental and easy to review.

**Success Criteria**
- The prompt has been properly claimed by moving it to `in-progress/`.
- Clear, reviewable output exists in `prompts/done/`.
- The models layer is visibly closer to the "no pre-defined derivative datasets" principle.

When finished, stop and wait for review. Do not start additional unrelated work.

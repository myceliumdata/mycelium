# Cursor Task: Clean up outdated "derivative dataset" language in documentation

**Objective**  
Remove or update references to the old "derivative dataset" model in documentation and comments so they align with the current Phase 1 direction.

**Background**  
See `docs/phase-1-direction.md`. We no longer pre-define derivative datasets. The old language (talking about creating derivative datasets, `DerivativeDatasetRef`, etc.) is now misleading.

**Scope (Strict)**

**In scope:**
- `README.md`
- `docs/` folder (except the review and workflow files in `prompts/done/`)
- Docstrings and comments in source code that describe high-level concepts (not implementation details of the current code)
- MCP server instructions / descriptions
- Any other user-facing documentation

**Out of scope:**
- Changing actual code behavior or variable names (unless they are purely in documentation strings)
- Historical git commit messages
- Files inside `prompts/done/` (these are historical records)

**Instructions**

1. Claim this task by moving the prompt file from `prompts/next/` to `prompts/in-progress/`.

2. Search the project for outdated language related to:
   - "derivative dataset"
   - "DerivativeDatasetRef"
   - "derivative_pending"
   - Creating or managing formal derivative datasets

3. Update the language to reflect the current model (specialist agents, `specialist_required`, deferred/non-core attributes, etc.).

4. Be conservative: If a reference is in a code comment that describes current implementation behavior (even if outdated conceptually), prefer leaving a clear note rather than deleting context.

5. Update `TODO.md` to mark this item as complete with a reference to this task.

**Output Requirements**

Create:
`prompts/done/2025-06-01-1735-documentation-cleanup-old-derivative-language/`

Required contents:
- `prompt.md` — Copy of this prompt
- `output.md` — Structured summary with:
  - List of all files modified
  - Examples of before/after language changes (3–5 good examples)
  - Any references you chose to leave as-is and why
  - Confirmation that `TODO.md` was updated
- `review-notes.md` (optional)

**Constraints**
- Do not change the behavior or structure of the code itself.
- Keep changes reviewable and incremental.
- If you find a very large number of outdated references, consider creating a follow-up prompt instead of doing everything in one pass.

**Success Criteria**
- Major user-facing documentation no longer promotes the old derivative dataset model.
- Changes are clear and well-documented.
- `TODO.md` is updated.

When finished, stop and wait for review.

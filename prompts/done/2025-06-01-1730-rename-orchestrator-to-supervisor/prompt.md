# Cursor Task: Rename orchestrator to supervisor for consistency

**Objective**  
Complete the naming alignment by renaming "orchestrator" references to "supervisor" across the codebase, as noted in the previous task and `TODO.md`.

**Background**  
See `docs/phase-1-direction.md` and the previous task output (`2025-06-01-1700-clean-derivative-references`). The direction document and our internal naming now use "supervisor" for the main coordination agent. The code still has several references to the old "orchestrator" name.

**Scope (Strict)**

**Allowed changes:**
- Rename the file `src/agents/orchestrator.py` to `src/agents/supervisor.py`
- Update the function name `orchestrator_agent` → `supervisor_agent`
- Update all imports and references across the project
- Update comments, docstrings, and strings where the term refers to the main coordination agent
- Update `TODO.md` to mark this item complete

**Explicitly out of scope (do not change):**
- Any architectural changes to how the supervisor works
- Changes to routing logic, storage access, or agent responsibilities
- Renaming in historical git history or commit messages

**Instructions**

1. Before starting any work, claim this task by moving the prompt file from `prompts/next/` to `prompts/in-progress/`.

2. Perform a thorough search for "orchestrator" (case-insensitive) across the codebase.

3. Rename the agent file and function as specified above.

4. Update all references consistently.

5. Update `TODO.md` to reflect that this item is complete, with a reference to this task.

6. Make clean, reviewable git commits with messages that reference this task number.

**Output Requirements**

Create the directory:
`prompts/done/2025-06-01-1730-rename-orchestrator-to-supervisor/`

Inside it, include at minimum:
- `prompt.md` — Copy of this prompt
- `output.md` — Structured summary containing:
  - List of all files that were renamed or modified
  - Any references you chose **not** to change and why
  - Confirmation that `TODO.md` was updated
  - Any remaining "orchestrator" mentions that are intentional (e.g., historical comments)
- `review-notes.md` (optional) — Any additional observations for Grok and Paul

**Constraints**
- Stay strictly within the scope defined above.
- Do not make any functional changes to the supervisor logic.
- If you discover that broader refactoring is needed, stop and document it instead of proceeding.

**Success Criteria**
- The agent file and primary references have been renamed to "supervisor".
- `TODO.md` is updated.
- Output is clear and reviewable.
- No out-of-scope changes were made.

When finished, stop and wait for review. Do not start additional unrelated work.

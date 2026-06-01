# Cursor Task: Add clear guidance for users with legacy `data/mycelium.db`

**Objective**  
Help users who have an existing `data/mycelium.db` from before the schema simplifications (removal of derivative tables and columns from the `people` table) understand what to do.

**Background**  
After the changes in task `2025-06-01-1700-clean-derivative-references`, the `people` table only contains `id`, `name`, and `employer`. Old databases may still have columns for `email`, `phone`, `title`, `extra_json`, plus the old `derivative_*` tables.

**Scope (Strict)**

**In scope:**
- `README.md`
- Possibly a new small file under `docs/` (e.g. `docs/database-notes.md`) if it feels cleaner
- Any relevant comments in `src/storage/core.py`

**Out of scope:**
- Writing actual migration code
- Changing the storage layer behavior
- Modifying the schema definition itself

**Instructions**

1. Claim the task by moving this prompt to `prompts/in-progress/`.

2. Investigate the current state of the database schema expectations in the code.

3. Add clear, user-friendly guidance that tells people with old databases what their options are. Suggested options to document:
   - Delete the old `data/mycelium.db` file (simplest for development)
   - Any manual steps needed if they want to preserve data
   - Warning that the application may behave unexpectedly or fail with an old schema

4. Place the guidance in the most visible appropriate place (likely the README under a "Database" or "Getting Started" section).

5. Update `TODO.md` to mark this item complete.

**Output Requirements**

Create:
`prompts/done/2025-06-01-1740-local-database-legacy-schema-note/`

Include:
- `prompt.md`
- `output.md` with:
  - Where you added the guidance
  - The exact text you added (or a link to the diff)
  - Any other places you considered and why you chose the final location
  - Confirmation that `TODO.md` was updated
- `review-notes.md` (optional)

**Constraints**
- Keep the guidance practical and non-alarmist.
- Do not promise migration support that doesn't exist.
- Prefer simple, clear instructions over complex ones.

**Success Criteria**
- Users who pull the repo and have an old `data/mycelium.db` will quickly understand their situation and options.
- The guidance is easy to find.

When finished, stop and wait for review.

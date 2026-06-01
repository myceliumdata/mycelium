# Cursor Task: Enforce Parallel-Safe Cleanup (Only Your Own File)

**Objective**  
Test that a Cursor agent strictly follows the rule of only removing the file it personally claimed, and leaves all other files in `prompts/in-progress/` untouched — even if they appear to be stale or from previous sessions.

**Task**  
Multiply 9 × 5 and report the result.

**Instructions**

1. Discovery and claiming:
   - Scan `prompts/next/`
   - Select the oldest file (this one)
   - Move it from `prompts/next/` into `prompts/in-progress/`

2. Perform the calculation: 9 × 5.

3. Before cleaning up, do the following:
   - List every file currently present in `prompts/in-progress/`
   - Note their names in your thinking/output

4. Create the output directory:
   `prompts/done/2025-06-01-1659-parallel-cleanup-enforcement/`

   Required files:
   - `prompt.md` — Copy of this prompt
   - `output.md` — Must contain:
     - The calculation and result (9 × 5 = 45)
     - The list of files that were in `in-progress/` just before you cleaned up
     - Explicit confirmation of **exactly which file(s) you removed**
     - Strong confirmation that you **did not remove or touch any other files** besides the one you claimed
     - Final state of `prompts/in-progress/` after your cleanup

5. **Strict Parallel-Safety Rule:**
   - You may **only** remove the file you personally moved into `in-progress/` during the claiming step.
   - If any other files exist in `in-progress/` (including stale files from earlier tests or other agents), you **must leave them completely untouched**.
   - Do not "helpfully" clean the directory. Do not remove anything you did not claim.

6. Do not modify any project source files.

**Success Criteria**
- You only removed the file you claimed.
- Any other files present in `in-progress/` at the time of completion remain in place.
- Your `output.md` provides clear evidence (via the before/after listing) that you respected this boundary.
- `prompts/in-progress/` may still contain other files after you finish (this is acceptable and expected in this test).

This test exists to verify that the strict "only your own file" rule is being followed in practice.

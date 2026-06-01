# Cursor Task: Test the Agent Handoff Workflow

**Objective**  
Validate that the entire Cursor agent handoff system works correctly before using it for real work.

**Task**  
Multiply the numbers 7 and 8, then report the result.

**Instructions**

1. **Before doing anything else**, follow the claiming process:
   - Scan `prompts/next/`
   - Identify the oldest file (this one, sorted alphabetically)
   - Move this file from `prompts/next/` into `prompts/in-progress/`

2. Perform the calculation: 7 × 8.

3. Create the following directory and files:

   `prompts/done/2025-06-01-1650-test-workflow/`

   Required contents:
   - `prompt.md` — A copy of this entire prompt
   - `output.md` — A short, clear summary containing:
     - The calculation you were asked to perform
     - The result
     - Confirmation that you moved this prompt to `in-progress/`
     - The exact path where you wrote the output
     - Any observations about the workflow

4. Do **not** make any changes to the actual project code (src/, docs/, etc.). This is purely a workflow test.

5. Once finished, remove this file from `prompts/in-progress/` (or leave it — either is acceptable for the test).

**Success Criteria**
- You correctly claimed the task by moving the file.
- You produced clean output in the expected `prompts/done/` location.
- The output clearly shows you understood and followed the workflow.

This is a test. Keep it simple and focused on validating the handoff system.

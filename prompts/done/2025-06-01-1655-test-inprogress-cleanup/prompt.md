# Cursor Task: Test In-Progress Cleanup

**Objective**  
Verify that Cursor correctly cleans up the `prompts/in-progress/` directory after completing a task.

**Task**  
Add the numbers 12 and 34, then report the result.

**Instructions**

1. Follow the standard discovery process:
   - Scan `prompts/next/`
   - Select the oldest file (this one)
   - Move it from `prompts/next/` into `prompts/in-progress/`

2. Perform the calculation: 12 + 34.

3. Create the output directory:
   `prompts/done/2025-06-01-1655-test-inprogress-cleanup/`

   Required files:
   - `prompt.md` — Copy of this prompt
   - `output.md` — Summary including:
     - The calculation performed and result
     - Confirmation that the prompt was moved to `in-progress/`
     - Confirmation that the file was **removed from `in-progress/`** after completion
     - The location of all deliverables

4. **Critical requirement (this is the point of the test):**
   - After creating the deliverables in `prompts/done/`, you **must** delete/remove the file from `prompts/in-progress/`.
   - When this task is complete, `prompts/in-progress/` should be empty.

5. Do not modify any project source files.

**Success Criteria**
- Correct claim via move to in-progress
- Correct output created in the done directory
- `prompts/in-progress/` is empty after you finish
- Your `output.md` explicitly confirms the cleanup step

This test is specifically to validate the new rule that in-progress must be cleaned up on completion.

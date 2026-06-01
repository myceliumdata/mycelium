# Cursor Task: Test Parallel-Safe Cleanup (Only Remove Your Own File)

**Objective**  
Validate that when multiple tasks are in progress, a Cursor agent only removes the specific file it claimed and does **not** touch any other files in `prompts/in-progress/`.

**Task**  
Multiply 6 × 7 and report the result.

**Instructions**

1. Follow the normal discovery and claiming process:
   - Scan `prompts/next/`
   - Select the oldest file (this one)
   - Move it from `prompts/next/` into `prompts/in-progress/`

2. Perform the calculation: 6 × 7.

3. Create the output directory:
   `prompts/done/2025-06-01-1658-parallel-safe-cleanup/`

   Required files:
   - `prompt.md` — Copy of this prompt
   - `output.md` — Summary that must include:
     - The calculation and result
     - Confirmation of which file you claimed and moved
     - Explicit confirmation that you **only removed your own claimed file** from `in-progress/`
     - Confirmation that you did **not** remove any other files that were present in `in-progress/` at the time of completion
     - The final state of `prompts/in-progress/` after you finished

4. **Critical Parallel-Safety Rule (this is the main point of the test):**
   - You are **only** allowed to remove the exact file you personally claimed.
   - If any other files exist in `prompts/in-progress/` when you finish (stale files, files claimed by other Cursor agents/sessions, etc.), you **must leave them completely untouched**.
   - Do not empty the directory. Do not clean up "on behalf of" anyone else. Over-cleaning will break parallel execution.

5. Do not modify any project source code outside of the required prompt artifacts.

**Success Criteria**
- You correctly claimed only this task.
- You removed **only** the file you claimed from `in-progress/`.
- Any other files that existed in `in-progress/` at completion time remain untouched.
- Your `output.md` clearly documents that you respected the "only clean your own file" rule.
- `prompts/done/2025-06-01-1658-parallel-safe-cleanup/` contains the required files.

This test exists to prevent dangerous over-cleaning behavior when multiple Cursor agents are working in parallel.

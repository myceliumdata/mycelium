# Review: 2025-06-01-1655-test-inprogress-cleanup

**Reviewers:** Grok + Paul  
**Date:** June 1, 2025

## Summary

This was the second test, focused on validating that `prompts/in-progress/` is properly cleaned up after task completion.

**Result:** The test passed the basic cleanup requirement. `prompts/in-progress/` was empty after completion.

## What Worked Well

- Cursor correctly followed the claiming process.
- It performed the requested calculation (12 + 34 = 46).
- It created the proper output structure in `prompts/done/`.
- It did remove its own claimed file from `in-progress/`, leaving the directory empty.
- It proactively cleaned up a stale file from the previous test (2025-06-01-1650). While not strictly required, this left the system in a clean state.

## Issues / Observations

1. **Over-cleaning risk identified**
   - During review of this test, we realized a potential problem for parallel execution:
     - Cursor removed not only its own file, but also a stale file left by a prior test.
   - While helpful in this isolated case, this behavior could be dangerous if multiple Cursor agents (or multiple sessions) are working concurrently.
   - One agent could accidentally delete another agent's claimed work in `in-progress/`.

2. **Instruction gap**
   - Previous instructions said to make `in-progress/` empty on completion.
   - This is too broad and unsafe for parallel use.

## Decisions Made

- Strengthened the cleanup rule across all instruction layers:
  - `prompts/WORKFLOW.md`
  - `.cursor/rules/04-cursor-workflow.mdc`
  - `.cursorrules` (cheat sheet)
- New rule: Each agent may **only** remove the specific file it personally claimed. It must never touch any other files in `in-progress/`, even if they appear stale.
- Created a new dedicated test (`2025-06-01-1658-parallel-safe-cleanup.md`) to specifically validate this stricter "only clean your own file" behavior.

## Action Items

- [x] Update instructions for parallel safety
- [x] Create follow-up test for the new rule (2025-06-01-1658-parallel-safe-cleanup.md)
- [x] Create additional enforcement test (2025-06-01-1659-parallel-cleanup-enforcement.md)
- [ ] Run the new parallel-safe cleanup tests
- [ ] Monitor behavior when multiple files exist in `in-progress/`

## Overall Assessment

Good progress. The test succeeded in its primary goal (cleanup happened), but more importantly, it surfaced a critical parallel execution issue before we hit it in real work. This is exactly why we are running these workflow tests.

The system is becoming more robust for concurrent Cursor agent usage.

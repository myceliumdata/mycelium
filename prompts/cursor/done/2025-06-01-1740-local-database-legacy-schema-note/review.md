# Review: 2025-06-01-1740-local-database-legacy-schema-note

**Reviewers:** Grok + Paul  
**Date:** June 1, 2025

## Summary

This task added clear guidance for users who have an existing `data/mycelium.db` created before the recent schema simplifications.

**Result:** Practical and well-placed.

## What Went Well

- Created a dedicated, clear `docs/database-notes.md` with:
  - Current schema explanation
  - Description of what legacy files may contain
  - Simple recommended actions (delete for development)
  - Honest note that there is no built-in migration in Phase 1
- Added a one-line pointer in the README under Quick start.
- Added a pointer in the module docstring of `src/storage/core.py`.
- `TODO.md` was updated with a reference to this task.
- Guidance is practical, non-alarmist, and easy to find.

## Observations

- Creating a separate `database-notes.md` was a good decision rather than bloating the main README.
- The note correctly distinguishes between the application database and the separate checkpoints database.

## Recommendations

- This item is complete.
- The guidance should help reduce confusion for anyone pulling the repo with an old database.

**Status:** Reviewed and accepted.
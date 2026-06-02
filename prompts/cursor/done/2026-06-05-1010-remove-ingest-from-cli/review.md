# Review: 2026-06-05-1010-remove-ingest-from-cli

**Status:** Approved.

## What was done
- Removed `ingest` subparser, arguments, `_load_person_data` function, and the ingest dispatch block from `src/main.py`.
- CLI now only has `query` and `seed`.
- Help text and comments cleaned.

## Code quality
- Clean removal.
- Query path untouched.
- Verification in output (help shows query/seed) is good.

## Issues / Notes
- The batch commit included this with others; output is concise but accurate.
- No scope creep.
- Seed command preserved, which is good (not related to ingest).

**Recommendation:** Approve. No changes needed.

Reviewed by Grok.

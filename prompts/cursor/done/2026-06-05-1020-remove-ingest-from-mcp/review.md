# Review: 2026-06-05-1020-remove-ingest-from-mcp

**Status:** Approved.

## What was done
- Removed `submit_person_data` tool, its registration, docstrings, examples, and related checks from `src/mycelium_mcp/server.py`.
- Server instructions cleaned to mention only queries.
- `query_person` and schema resources remain.

## Code quality
- Thorough removal of the tool.
- Import of Person still there (used by query_person), fine.
- Verification note about tool list is appropriate.

## Issues / Notes
- The docstring update left a comment about "id" which was from previous, but since the tool is gone, the remaining example in query_person docstring should be reviewed for cleanliness (but not critical).
- Batch execution ok.

**Recommendation:** Approve.

Reviewed by Grok.

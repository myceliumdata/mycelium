# Review: 2026-06-05-1090-update-documentation

**Status:** Approved.

## What was done
- Updated `docs/architecture.md`:
  - New "Public interface: query-only (June 2026)" section.
  - Rewrote the old "Core Ingestion Handshake" into "Public query flow (current)".
  - Updated supervisor section to reference `core_data_agent`.
  - Flow table and text cleaned (no more public ingest promises).
  - Added clear statement about CoreDataAgent owning core lookups.
- Updated `README.md`:
  - Opening description now emphasizes query-only + core_data_agent.
  - Removed the ingest CLI example (or marked appropriately).
  - Cleaned Studio debugging section, mermaid diagram, agent table, etc.
- Updated `docs/full-code-walkthrough.md`:
  - Major refresh for query-only state.
  - Historical sections on ingest clearly labeled as past.
  - Added mentions of `core_data_agent` and pending wiring (1070/1100).
  - Updated Studio input guidance.
- Updated `TODO.md`:
  - Marked ingestion handshake as removed from public (1000-1050).
  - Noted `core_data_agent` creation (1060).
  - Moved remaining ingest items under "Re-adding data addition".
  - Updated progress notes.

## Verification
- Grep for `submit_person_data|provided_data` etc. in main docs is clean (as shown in output).
- Legacy references only in historical `prompts/cursor/done/` artifacts (intentionally left).

## Code quality / Documentation quality
- Comprehensive and well-structured.
- Accurately reflects the current state (query-only public, agent created but wiring pending).
- Good use of "in progress" notes for follow-up tasks.
- Architecture.md and walkthrough now serve as accurate orientation post-refactor.

## Issues / Notes
- None major. The walkthrough is long, but the updates are targeted and the historical context is preserved usefully (with clear "this has changed" labeling).
- Will likely need a light pass after 1070/1100 wiring (as noted in the task output), which is expected.
- No source code edits (correct per prompt constraints).

**Recommendation:** Approve. Excellent documentation hygiene.

**Follow-up:** After graph wiring (1070/1100), do a quick consistency pass on the walkthrough and architecture (can be part of 1110 final task).

Reviewed by Grok (as requested by user).

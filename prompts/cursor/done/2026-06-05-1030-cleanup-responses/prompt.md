# Task: Remove ingest-related response builders from responses.py

## Objective
Clean `src/agents/responses.py` of all ingest-specific functions (`response_ingest_success`, `response_ingest_failure`, `_ingest_guidance_message`, and any related logic). Update the remaining functions (`response_found`, `response_not_found`, `response_non_core`) so their messages and debug output no longer reference adding data or ingestion. The module should now only produce query responses.

## Constraints
- Public responses for queries must be clean (no "how to ingest" guidance in not-found messages).
- Keep the private `_make_response` and `debug_for_query` helpers if still useful.
- Do not change the signature or behavior of the three query response functions beyond removing ingest language.
- This is pure cleanup after public ingest removal.

## Context
- These functions were used by the routing logic for the two ingest outcomes and the "not found → suggest ingest" message.
- After routing and supervisor simplification (parallel tasks), these will no longer be called for public paths.
- The not-found message currently gives ingestion advice; that must go.

## Exact Steps
1. Edit `src/agents/responses.py`:
   - Delete `response_ingest_success`, `response_ingest_failure`, and `_ingest_guidance_message`.
   - Update `response_not_found` to produce a simple "not found" message without any suggestion to add data.
   - Update `debug_for_query` calls inside the remaining functions if they hard-coded ingest outcomes.
   - Clean any top-level docstring or comments that mention ingestion.
   - Leave `response_found` and `response_non_core` intact except for any ingest language.
2. The file should still export or allow import of the three query builders used by routing.
3. Do not touch callers (routing, supervisor, etc.) — they will be updated in their own tasks.

## Required Output
- Standard done/ layout with prompt.md, output.md (include diff and before/after message examples), etc.
- Claim via move to in-progress/ first.

Follow `prompts/cursor/WORKFLOW.md` claiming rules strictly.

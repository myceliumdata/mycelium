# Review: 2026-06-05-1040-simplify-routing

**Status:** Approved.

## What was done
- `evaluate_supervisor_turn` simplified to only lookup paths: found / not-found / non-core.
- Removed all `provided_data`, validation, ingest branches and imports.
- `SupervisorDecision` now always "response" (no more route_enrich).
- Docstring updated.

## Code quality
- The logic is now much cleaner for query-only.
- Note in output about graph still having nodes is accurate (addressed in 1070).

## Issues / Notes
- Imports `Person` for the dataclass — still needed for returning the person in decision.
- Good that it still delegates to CoreIdentity (to be replaced by core_data_agent later).

**Recommendation:** Approve.

Reviewed by Grok.

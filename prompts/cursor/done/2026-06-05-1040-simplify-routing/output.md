# Output: Simplify routing (query-only)

## Summary

`evaluate_supervisor_turn` now only: lookup → found / not-found / non-core. Removed validation, `provided_data`, and ingest response imports. `SupervisorDecision` is always a `response` (no `action` / `route_enrich`).

## Note

Graph still contains enrich/validator nodes until task 1070; supervisor no longer routes to them.

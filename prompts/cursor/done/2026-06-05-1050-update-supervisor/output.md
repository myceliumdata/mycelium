# Output: Update supervisor (query-only)

## Summary

Removed `route_enrich` branch from `_apply_decision`. Supervisor always applies a respond payload. Docstrings updated for query-only coordination.

## Note

Async `to_thread` pattern preserved for CoreIdentity lookups.

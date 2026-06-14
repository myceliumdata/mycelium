# Admin UI polish — suggestion refresh, Run layout, invalid lookup param

## Summary

Closed three non-blocking review nits from slice `1300`: suggestion clicks refresh drill-down via `GET /status` in active contexts, Step 1 **Run** sits on its own row, and malformed `lookup` on `GET /status` returns 400.

## Nits addressed

| Nit | Fix |
|-----|-----|
| **N1** | `applySuggestion` calls `refreshInspectFromForm` when `lastInspectKey` set, or `refreshQueryDrilldownWith` when `queryDrilldownActive` — no `POST /query` |
| **N2** | Step 1 **Run** moved to `.panel-actions` row below attributes / confirm checkbox |
| **N3** | `GET /status?lookup=not-json` → 400 `"lookup must be a JSON object"` |

## Changes

| File | Change |
|------|--------|
| `admin-ui/src/App.tsx` | `refreshInspectFromForm` helper; suggestion refresh branches; Run on own row |
| `admin-ui/src/styles.css` | `.query-step-extras` column layout; `.panel-actions` separate from extras |
| `src/mycelium_admin/server.py` | `HTTPException` on invalid lookup JSON |
| `tests/test_admin_daemon.py` | `test_status_lookup_invalid_json_returns_400` |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 406 passed, 26 deselected
```

## For Grok + Paul

- N1–N3 from `1300` review addressed.
- `test_status_lookup_map_single_match` still passes (valid lookup unchanged).
- **Not committed** — awaiting review.

Suggested commit message:

```
polish(admin-ui): refresh inspect on suggestion and fix step-1 layout

Re-fetch status after drill-down suggestion in inspect/query contexts;
move Step 1 Run below attributes; return 400 for invalid status lookup JSON.
```

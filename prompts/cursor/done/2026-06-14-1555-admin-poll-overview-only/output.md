# Admin UI — Poll network overview only

## Summary

Decoupled background polling from entity inspect/drill-down. The 3s poll and tab-visibility refresh now call bare `GET /status` (optional `category` only). Inspect fetches run only on explicit user actions.

## Root cause fixed

`statusQueryParams()` piggybacked `id`/`lookup` from `statusParams` onto every poll when `queryDrilldownActive` or `lastInspectKey` was set — flooding daemon logs after step 1 or Inspect.

## Changes

### `admin-ui/src/App.tsx`

- Split state: `overviewStatus` (polled) vs `inspectStatus` (on-demand)
- Removed `statusQueryParams()`; added `overviewPollParams()` for poll/visibility only
- `pollStatus` / `refreshOnVisible` → update `overviewStatus` only
- `fetchInspectStatusNow()` → update `inspectStatus` only (Inspect, step 1, suggestions, category filter while drill active)
- `EntityDrilldown` reads `inspectStatus`, not polled overview
- `runQueryStep1` captures `modeForDrill`, `idForDrill`, `lookupValuesForDrill` **before** clearing form state, then calls `refreshQueryDrilldownWith` with captured values

### `README.md`

- Admin UI poll note: overview-only poll; drill-down on Inspect / post-step-1
- Status endpoint flags: `?id=` / `?lookup=` (not `?entity=`)

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 401 passed, 26 deselected
```

## Manual verification (Paul)

1. Open admin, fill lookup, click **Run** step 1
   - **Before:** repeated `GET /status?lookup=…` every 3s
   - **After:** one `GET /status?lookup=…` after step 1, then `GET /status` every 3s

2. Click **Inspect** with lookup filled
   - One `GET /status?lookup=…` (or `?id=`)
   - Poll continues as bare `GET /status`

3. Run external MCP query; watch admin Overview specialist counts update on poll without lookup params in poll URLs

Example log pattern (after fix):

```
GET /status?lookup=%7B%22name%22%3A%22Andrea%20Kalmans%22%7D   # once after Run step 1
GET /status                                                  # every 3s
GET /status
GET /status
```

## For Grok + Paul

- Standalone admin fix — no server changes
- Safe to merge before slice **1560** polish

Suggested commit message:

```
fix(admin-ui): poll network overview only; inspect status on demand
```

- **Committed** after Grok review (see `review.md`).

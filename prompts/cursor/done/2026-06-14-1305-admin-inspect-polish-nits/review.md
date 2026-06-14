# Review: 2026-06-14-1305-admin-inspect-polish-nits

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 406 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 406 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| N1: `refreshInspectFromForm` + suggestion refresh branches | ✅ |
| N2: Step 1 **Run** in separate `.panel-actions` row | ✅ |
| N3: `HTTPException` 400 + `test_status_lookup_invalid_json_returns_400` | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `admin-ui/src/App.tsx`
- `admin-ui/src/styles.css`
- `src/mycelium_admin/server.py`
- `tests/test_admin_daemon.py`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| N1: Suggestion refreshes drill-down via `GET /status` in active contexts | ✅ (see edge-case nit) |
| N2: Step 1 Run on separate row below attributes | ✅ |
| N3: Malformed `lookup` → 400 + smoke test | ✅ |
| `./bin/ci-local` green | ✅ |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| `test_status_lookup_map_single_match` still valid | ✅ (CI green) |
| Inspect vs query panel separation unchanged | ✅ |
| No `POST /query` on suggestion click | ✅ |

## Tests

| Test | Coverage |
|------|----------|
| `test_status_lookup_invalid_json_returns_400` | Malformed string → 400 + detail message |
| Gap | No smoke for valid JSON non-object (e.g. `lookup=[]`) — server handles via same 400 path |

## Design critique

**Strong:** `refreshInspectFromForm` dedupes `onInspect` and the inspect suggestion path cleanly. `refreshQueryDrilldownWith` accepts explicit mode/values so suggestion refresh uses computed `nextLookup` before React state flushes — correct. N3 error is clear and chained from `JSONDecodeError`. Layout split matches 1300 spec diagram.

**Edge case (nit):** `applySuggestion` checks `lastInspectKey` before `queryDrilldownActive`. If the user **Inspect**s in Entity lookup then **Run**s step 1 in Run query, both flags are set; a suggestion click takes the inspect branch and calls `setQueryDrilldownActive(false)`, hiding the query drill-down. Fix: prefer `queryDrilldownActive` first, or clear `lastInspectKey` when activating query drill-down.

## Nits

| # | Nit | Severity |
|---|-----|----------|
| N4 | Suggestion branch priority when `lastInspectKey` and `queryDrilldownActive` both set | Polish |
| N5 | Add smoke for non-object JSON (`lookup=[]`) if we want symmetric 400 coverage | Polish |

## For Paul

**Commit message:**

```
polish(admin-ui): refresh inspect on suggestion and fix step-1 layout

Re-fetch status after drill-down suggestion in inspect/query contexts;
move Step 1 Run below attributes; return 400 for invalid status lookup JSON.
```

**Next:** Manual gate Check 0c-vi still applies. Queue empty unless you want a tiny follow-up for N4 branch order.

**Git:** Local commit only — no push until you ask.
# Admin UI polish — suggestion refresh, Run layout, invalid lookup param

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context:** Grok review of slice `1300-admin-restore-inspect-split-query-layout` ([`review.md`](../done/2026-06-14-1300-admin-restore-inspect-split-query-layout/review.md)) logged three **non-blocking** nits (N1–N3). Parent slice is on `main` (`4dc5369`). This polish pass closes them without changing inspect vs query separation from 1300.

**Prerequisites:** `1300` committed on `main`.

---

## Tasks (all three required)

### N1 — Suggestion click refreshes drill-down (no `POST /query`)

**Problem:** `applySuggestion` in `admin-ui/src/App.tsx` only updates resolve form fields. In **Entity lookup**, user must click **Inspect** again after picking a suggestion.

**Fix:** After updating fields in `applySuggestion`, refresh status read-only when a drill-down context is active:

| Context | After suggestion click |
|---------|------------------------|
| Entity lookup (`lastInspectKey` set) | Re-run the same path as **Inspect**: `inspectStatusParams` → `setStatusParams` → `setLastInspectKey` (updated display key) → `fetchStatusNow` — **no** `POST /query`, **no** `setQueryResult` |
| Query panel (`queryDrilldownActive`) | Call existing `refreshQueryDrilldown()` |
| Neither (query panel before first Run) | Fields only — unchanged |

Prefer extracting a small helper (e.g. `refreshInspectFromForm()`) shared by `onInspect` and the inspect branch of `applySuggestion` to avoid duplicated param assembly.

**Do not** auto-run `runQueryStep1` on suggestion click.

### N2 — Step 1 Run on its own row

**Problem:** Step 1 **Run** sits in the same flex row as requested attributes (`query-step-extras`).

**Fix:** In `admin-ui/src/App.tsx` + `admin-ui/src/styles.css`:

- Keep **Requested attributes** (and `confirm_new_entity` when shown) in `query-step-extras`.
- Move the Step 1 **Run** button to a separate row below (reuse `.panel-actions` pattern from Entity lookup **Inspect**, or equivalent).
- Layout target (Run query panel step 1):

```
│  Requested attributes: [____________]         │
│  [ ] Confirm new entity (when shown)          │
│  [ Run ]                                      │  ← own row, left-aligned
```

Entity lookup **Inspect** layout unchanged.

### N3 — Reject malformed `lookup` on `GET /status`

**Problem:** Invalid `lookup` JSON is silently ignored; response looks like a generic network overview.

**Fix in `src/mycelium_admin/server.py` `status` handler:**

- If `lookup` query param is **non-empty** and:
  - `json.loads` raises `JSONDecodeError`, **or**
  - parsed value is **not** a `dict`
  → return **400** with a clear JSON/detail message (e.g. `"lookup must be a JSON object"`).
- Valid JSON object that parses to empty bind map after strip (all values blank) may still return overview — same as today.
- Valid lookup behavior unchanged (`test_status_lookup_map_single_match` must still pass).

Add smoke test in `tests/test_admin_daemon.py`:

- `test_status_lookup_invalid_json_returns_400` — e.g. `lookup=not-json` → 400.

---

## Read first

- `admin-ui/src/App.tsx` — `onInspect`, `applySuggestion`, `refreshQueryDrilldown`, query step 1 markup
- `admin-ui/src/styles.css` — `.query-step-extras`, `.panel-actions`
- `src/mycelium_admin/server.py` — `GET /status` lookup parsing
- `prompts/cursor/done/2026-06-14-1300-admin-restore-inspect-split-query-layout/review.md` — nits N1–N3

---

## Scope boundaries

**May modify:**

- `admin-ui/src/App.tsx`
- `admin-ui/src/styles.css`
- `src/mycelium_admin/server.py`
- `tests/test_admin_daemon.py`

**Out of scope:**

- `TODO.md`
- MCP / CLI
- Re-merging Entity lookup and Run query panels
- New features beyond N1–N3

---

## Verification

```bash
./bin/ci-local
./bin/restart-admin crm
```

Manual:

1. **Entity lookup** → Andrea @ Wrong Corp → **Inspect** → click a suggestion → drill-down refreshes without **Inspect** click and **no** `POST /query` in DevTools.
2. **Run query** → step 1 after a prior Run with drill-down → click suggestion → drill-down refreshes via `GET /status` only.
3. **Run query** → before first Run → suggestion from query result populates fields only (no status refresh until Run).
4. Step 1 **Run** appears on its own row below attributes / confirm checkbox.
5. `curl 'http://127.0.0.1:8741/status?lookup=not-json'` → 400.

---

## Governance

- Do not edit `TODO.md`.
- In `output.md`, add **For Grok + Paul**: confirm N1–N3 addressed; note test added for N3.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1305-admin-inspect-polish-nits/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- N1: Inspect-context suggestion click refreshes drill-down via `GET /status` only
- N2: Step 1 Run on separate row below attributes
- N3: Malformed `lookup` → 400 + smoke test
- `./bin/ci-local` green

Suggested commit message:

```
polish(admin-ui): refresh inspect on suggestion and fix step-1 layout

Re-fetch status after drill-down suggestion in inspect/query contexts;
move Step 1 Run below attributes; return 400 for invalid status lookup JSON.
```
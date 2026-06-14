# Admin UI — Poll network overview only (fix aggressive inspect refresh)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` before starting.

**Context:** Paul reported admin daemon logs flooded with `GET /status?lookup=…` every 3s after **Run query** step 1 or **Inspect**. Background poll should refresh **network overview** (specialist counts, ontology, registry), not re-run entity inspect/drill-down. `POST /query` is user-initiated only — do not change query behavior.

**Prerequisite:** None (standalone admin-ui fix). May run before slice **1560** polish.

---

## Objective

Decouple **background polling** from **inspect/drill-down** status fetches. The 3s interval and tab-visibility refresh must call bare `GET /status` (optional `category` filter only), never `id` or `lookup` params.

---

## Read first

- [`admin-ui/src/App.tsx`](../../admin-ui/src/App.tsx) — `statusQueryParams`, `pollStatus`, `refreshOnVisible`, `refreshQueryDrilldown`, `runQueryStep1`
- [`admin-ui/src/EntityDrilldown.tsx`](../../admin-ui/src/EntityDrilldown.tsx) — consumes `status` prop
- [`README.md`](../../README.md) — “polls `/status` every 3s … specialists appear as MCP/CLI queries populate storage” (overview intent)
- [`prompts/cursor/done/2026-06-14-1300-admin-restore-inspect-split-query-layout/review.md`](../../prompts/cursor/done/2026-06-14-1300-admin-restore-inspect-split-query-layout/review.md) — prior `statusQueryParams()` gating (now wrong for poll)

---

## Root cause (confirmed)

```typescript
// App.tsx — poll uses drill params when inspect or query drill-down active
const statusQueryParams = useCallback((): StatusFetchParams => {
  if (lastInspectKey || queryDrilldownActive) {
    return { ...statusParams, category: entityCategoryLimit || undefined };
  }
  return {};
}, [...]);

// pollStatus + refreshOnVisible both call fetchStatus(statusQueryParams())
```

After step 1, `refreshQueryDrilldown()` sets `queryDrilldownActive = true` and `statusParams` with lookup → every 3s poll hits `/status?lookup=…`.

---

## Locked design

### 1. Two status roles

| Role | Endpoint | When updated |
|------|----------|--------------|
| **Overview** | `GET /status` or `?category=` | Initial load, 3s poll, tab visible, manual refresh if present |
| **Inspect / drill-down** | `GET /status?id=` or `?lookup=` | **Explicit only:** Inspect button, after step 1 (once), suggestion apply, category filter change while drill active |

Do **not** piggyback inspect params on poll.

### 2. State shape (recommended)

Split React state:

- `overviewStatus` — polled; drives Overview (entity count, specialists, ontology presence)
- `inspectStatus` — optional `null` when no drill target; drives `EntityDrilldown` in entity-lookup and query panels

Alternatively keep one `status` for overview and a separate `inspectStatus` only when `lastInspectKey || queryDrilldownActive`. Pick the smallest clear diff.

**EntityDrilldown** must read **inspect** snapshot, not the polled overview (or it will lose `entity_fields` when overview has no `resolve`).

### 3. Poll / visibility (unchanged timing)

- Keep `POLL_MS = 3000`, `document.hidden` skip, `statusInFlight` guard
- `pollStatus` → `fetchStatus({ category: entityCategoryLimit || undefined })` only (or `{}`)
- `refreshOnVisible` → same for status; still fetch health + capabilities
- Remove `statusQueryParams()` from poll paths entirely (delete helper if unused)

### 4. Explicit inspect refresh (keep behavior)

| Action | Fetch |
|--------|-------|
| **Inspect** (`onInspect`) | `inspectStatusParams` → `fetchStatus(params)`; set `lastInspectKey` |
| **Run step 1** success | One inspect fetch using lookup/id **from the query just run** (capture in local vars **before** clearing form state); set `queryDrilldownActive` |
| **Suggestion click** | `refreshInspectFromForm` or `refreshQueryDrilldownWith` (unchanged intent) |
| **Category limit** while drill active | Re-fetch inspect with same target + new category |

### 5. Step 1 ordering fix

`runQueryStep1` currently clears `lookupValues` then calls `refreshQueryDrilldown()` which closes over stale/cleared values. Capture:

```typescript
const lookupForDrill = resolveMode === "lookup" ? buildLookupPayload(...) : undefined;
const idForDrill = resolveMode === "id" ? queryRegistryId.trim() : undefined;
// ... runQuery ...
// then refresh inspect once with captured lookup/id, not post-clear form state
```

### 6. Query behavior

- **No** auto `POST /query` on poll or status refresh
- Step 2 deliver unchanged (user click only)

### 7. README

One-line update if needed: poll refreshes **network overview**; entity drill-down refreshes on Inspect / post-step-1 only.

---

## Tests

No new Python smokes required. Verification:

```bash
./bin/ci-local   # admin-ui tsc + vite build must pass
```

Manual (document in `output.md`):

1. Open admin, fill lookup, **Run** step 1 → daemon shows **one** `GET /status?lookup=…`, then repeated `GET /status` **without** lookup every 3s
2. **Inspect** → one lookup/id status fetch; poll still bare `/status`
3. Overview specialist counts still update on poll after external MCP query (no lookup in poll URLs)

---

## Out of scope

- `src/mycelium_admin/server.py` (server is fine)
- `TODO.md`
- Program 3 polish items (1560)
- Splitting `fetchError` vs `pollError` (existing nit)

---

## Deliverable

`prompts/cursor/done/2026-06-14-1555-admin-poll-overview-only/`

Suggested commit:

```
fix(admin-ui): poll network overview only; inspect status on demand
```

**For Grok + Paul in `output.md`:** manual verification steps + before/after log snippet.
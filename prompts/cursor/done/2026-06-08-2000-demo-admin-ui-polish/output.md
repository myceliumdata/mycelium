# Demo admin UI polish

## Summary

Polished `admin-ui` for scannable demos: Overview shows three ✅/❌ status lines only, secondary panels start collapsed, and `/status` polls every 3s (silent, visibility-aware) so specialist rows appear after MCP/CLI queries without manual Refresh.

## Before → after

| Area | Before | After |
|------|--------|-------|
| Overview | Seed + inline ontology categories + specialist hint | `✅ Seed (N)`, `✅/❌ Ontology`, `✅/❌ Specialists` only |
| Specialist expand | Ontology examples + storage | Storage only: fields tracked + status counts |
| Guide card | Ontology `<details open>` | Author guide + Ontology both collapsed by default |
| Entity lookup | Always open card | Collapsed `<details>`; category option **All** |
| Refresh | Full reload with Loading flash | Initial load shows Loading; polls silent; manual Refresh refetches all three endpoints |

## Auto-refresh behavior

- **Interval:** 3s `GET /status` with current `entity` / `category` query params (same as manual refresh scope).
- **Pause:** `document.hidden` skips ticks; resumes + immediate fetch when tab visible.
- **Overlap:** Skips tick if a status request is already in flight.
- **Errors:** Subdued `poll-error` line; last good data retained; retries next interval.
- **State preserved:** Controlled `<details>` for specialist expands, entity lookup, guide, ontology — polls update `status` without resetting open/closed or input values.
- **`/capabilities`:** Initial load + manual Refresh only (not polled).

## Files changed

| File | Change |
|------|--------|
| `admin-ui/src/App.tsx` | Layout restructure, controlled collapse state, polling |
| `admin-ui/src/styles.css` | Status lines, collapsible card, poll-error styles |

## Verification

```bash
cd admin-ui && npm run build   # ✓
```

Manual (Paul):

```bash
MYCELIUM_NETWORK=crm uv run mycelium-admin
cd admin-ui && npm run dev
uv run mycelium query --network crm --entity-key "Andrea Kalmans" --attributes email
# Specialist row should appear within ~3s without Refresh
```

## For Grok + Paul

- Mark **Admin UI polish** done in `TODO.md` (Cursor did not edit per governance).
- Optional follow-up: Vitest for poll skip-when-in-flight; Playwright E2E after storage populated.
- `formatCategoryExamples` remains in `format.ts` for potential reuse; no longer imported in `App.tsx`.

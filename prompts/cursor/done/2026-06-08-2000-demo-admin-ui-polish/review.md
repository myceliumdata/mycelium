# Review: Demo admin UI polish (`2026-06-08-2000`)

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Commit:** `3b36a4e`  
**Verdict:** **Approved**

---

## Scope check

| Requirement | Status |
|-------------|--------|
| Overview: `✅ Seed (N)`, `✅/❌ Ontology`, `✅/❌ Specialists` | ✅ |
| No inline ontology categories in Overview | ✅ |
| Specialist expands: storage only (no ontology copy) | ✅ |
| No “expand for storage detail” hint | ✅ |
| Guide + Ontology collapsed `<details>` in guide card | ✅ |
| Entity lookup collapsed by default | ✅ |
| Category option **All** | ✅ |
| 3s silent `/status` poll, visibility pause, in-flight skip | ✅ |
| Preserve expanded/collapsed + entity input state | ✅ |
| `/capabilities` on initial + manual Refresh only | ✅ |
| Governance: no `TODO.md` edit | ✅ |
| `output.md` + **For Grok + Paul** | ✅ |
| `npm run build` | ✅ |

---

## Verification (Grok re-run)

```text
cd admin-ui && npm run build  → success
```

Paul manual: daemon + `npm run dev` + query → specialist row within ~3s (acceptance per `output.md`).

---

## What looks good

- **Controlled `<details>`** for entity lookup, guide, ontology, and specialist rows — polls update `status` without collapsing user-expanded sections.
- **Poll design** — `statusInFlight` ref prevents overlap; `document.hidden` gate; immediate fetch on tab focus.
- **Overview** is genuinely scannable — three lines match CLI demo vocabulary; secondary noise moved to collapsed panels.
- **Governance followed** — roadmap note deferred to `output.md`.

---

## Issues

### Nit — manual Refresh errors use poll copy

- **File:** `admin-ui/src/App.tsx` — `loadFull()` catch sets `pollError`, so header **Refresh** failures read “Background refresh failed”.
- **Suggestion:** Use `fetchError` (or a dedicated `refreshError`) in `loadFull`; reserve `pollError` for interval polls only. Optional polish; not blocking.

---

## Out of scope for this review

- `bin/restart-admin` — queued separately (`2026-06-08-2100`); Paul running in parallel.

---

## Decision

**Approve.** Mark **Admin UI polish** done in `TODO.md`. Paul hands-on with `npm run dev` + live queries is the real acceptance test for auto-refresh.
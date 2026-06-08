# Review: Demo admin UI polish v3 (`2026-06-08-2300`)

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Commit:** `7097142`  
**Verdict:** **Approved**

---

## Scope check

| Requirement | Status |
|-------------|--------|
| No Refresh button in header | ✅ |
| No `network_root:` line | ✅ |
| `loadFull` / `onRefresh` removed | ✅ |
| Tab visible → silent health + status + capabilities | ✅ |
| `ontology_present` false→true → capabilities refetch | ✅ |
| 3s poll stays status-only | ✅ |
| `fetchError` initial mount only; background → `pollError` | ✅ |
| v2 behavior preserved | ✅ |
| Governance: no `TODO.md` edit | ✅ |
| `output.md` + **For Grok + Paul** | ✅ |
| `npm run build` | ✅ |

---

## Verification (Grok re-run)

```text
cd admin-ui && npm run build  → success
```

Paul manual: `./bin/restart-admin` — confirm header is clean and specialists still update within ~3s after query.

---

## What looks good

- **Capabilities without Refresh** — `refreshOnVisible` + `prevOntologyPresent` flip detection covers the two cases that matter for demos (tab return + ontology first appears).
- **In-flight guards** — `statusInFlight` / `capsInFlight` avoid pile-up; ontology flip uses separate `fetchCapabilitiesSilent`.
- **Header** — demo-friendly: title, badge, network label only.

---

## Issues

### Nit — visibility refresh may skip if poll in flight

- **File:** `admin-ui/src/App.tsx` — `refreshOnVisible` returns early when `statusInFlight.current`, so tab-focus full refresh can be skipped if a 3s poll is mid-request.
- **Impact:** Low — next poll or a later tab focus will catch up.
- **Suggestion:** Optional follow-up: queue visibility refresh after current in-flight completes, or use a separate ref for visibility bundle.

### Nit — dead CSS

- **File:** `admin-ui/src/styles.css` — `button.secondary` and `button.linkish` unused after Refresh removal.
- **Suggestion:** Remove in a future discretionary polish slice.

---

## Decision

**Approve.** Demo UI header is appropriately minimal; capabilities refresh strategy is sound for live demos.
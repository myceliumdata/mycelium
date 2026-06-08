# Demo admin UI polish v2

## Summary

Fixed Paul-reported bugs from hands-on testing: renamed UI “Ontology” → “Categories”, collapsed the guide card, unified disclosure arrows, fixed specialist expand (uncontrolled `<details>`), and hardened `fetchJson` against HTML responses.

## Before → after

| Issue | Fix |
|-------|-----|
| Overview said “Ontology” | `✅/❌ Categories` |
| Guide card always open | Wrapped in collapsible `<details>` (collapsed on load) |
| Inconsistent arrow sizes | Shared `.disclosure-summary` with `1.1em` `▸`/`▾` on all summaries |
| Specialist click showed `index.html` | Removed controlled `open`/`onToggle`; native toggle + stable `key={category}` |
| HTML in error banner on bad fetch | `fetchJson` detects HTML, throws short message; bodies truncated to 200 chars |

## Specialist expand fix

**Root cause:** Controlled `specialistExpanded` state fought native `<details>` toggle under React re-renders (poll every 3s), causing navigation/fetch oddities.

**Fix:** Uncontrolled specialist `<details>`; browser preserves open state across poll updates when `key={spec.category}` is stable.

**API hardening:** If `/status` returns SPA `index.html` (daemon down, wrong proxy), error is:
`Expected JSON from /status, got HTML — is mycelium-admin running?`

## Manual verification

```bash
./bin/restart-admin
# or: MYCELIUM_NETWORK=crm uv run mycelium-admin + npm run dev

# With specialists present:
# - Click contact (N) → expands in place, fields tracked visible
# - No full-page index.html flash
# - Poll updates counts within ~3s after query

cd admin-ui && npm run build   # ✓
```

## v1 behavior preserved

- 3s silent `/status` poll, visibility pause, `statusInFlight` skip
- `fetchError` vs `pollError` split
- Entity lookup + guide card collapsed on load
- Overview three status lines + specialist expands when ✅
- `/capabilities` on initial + manual Refresh only

## For Grok + Paul

- Mark **Admin UI polish v2** done in `TODO.md` (Cursor did not edit per governance).
- Optional: Vitest for `looksLikeHtml` / `truncateBody` in `api.ts`.
- Playwright E2E for specialist expand still deferred.

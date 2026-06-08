# Demo admin UI polish v3

## Summary

Simplified the demo header for non-engineer audiences: removed the manual **Refresh** button and **`network_root:`** debug line. Capabilities data stays current via tab-visibility refresh and ontology flip detection.

## Before → after

| Element | Before | After |
|---------|--------|-------|
| Header | Title + badge + network + Refresh | Title + badge + network only |
| Below header | `network_root: …` muted line | Removed |
| `/capabilities` refresh | Initial load + manual Refresh | Initial load + visibility + ontology flip |

## Capabilities refresh (replaces manual Refresh)

| Trigger | Fetches (silent) |
|---------|------------------|
| **Tab visible again** | `GET /health`, `GET /status` (with entity/category params), `GET /capabilities` |
| **Ontology appears** | `GET /capabilities` once when status poll sees `ontology_present` flip `false → true` |
| **3s interval** | `GET /status` only (unchanged) |

- `fetchError` — initial mount failures only
- `pollError` — background/visibility/capabilities failures (subdued banner)
- `statusInFlight` / `capsInFlight` prevent overlapping requests

## v2 preserved

Categories labels, collapsed cards, unified arrows, uncontrolled specialist details, `fetchJson` HTML guard, 3s status poll, visibility pause.

## Verification

```bash
cd admin-ui && npm run build   # ✓

./bin/restart-admin
# 1. No Refresh button, no network_root line
# 2. Run query → specialists update within ~3s
# 3. Fresh network: after first query creates ontology, Categories panel populates without reload
```

## For Grok + Paul

- Mark **Admin UI polish v3** done in `TODO.md` (Cursor did not edit per governance).
- Demo phase admin UI may be complete; any further polish is discretionary.

# Admin UI — restore entity inspect, split query, identical resolve form, layout fix

## Summary

Restored the **Entity lookup** (Inspect → `GET /status` only) and **Run query** (`POST /query`) as separate panels sharing an identical `ResolveForm`. Added `GET /status?lookup=…` for full MVR inspect parity. Split step 1 **Run** and step 2 **Deliver** buttons with stacked resolve layout.

## Changes

| Area | Change |
|------|--------|
| `admin-ui/src/ResolveForm.tsx` | Shared resolve block (radio + stacked inputs) |
| `admin-ui/src/EntityDrilldown.tsx` | Reusable drill-down table + version history |
| `admin-ui/src/App.tsx` | Two panels; separate inspect/query handlers; layout cleanup |
| `admin-ui/src/mvr.ts` | `inspectStatusParams`, `inspectDisplayKey`, `hasStatusTarget` |
| `admin-ui/src/api.ts` | `fetchStatus` accepts `lookup` object (JSON query param) |
| `admin-ui/src/styles.css` | `.resolve-inputs`, `.panel-actions`, `.query-step-extras` |
| `src/agents/entity_resolution.py` | `resolve_status_for_target_lookup()` |
| `src/network/introspection.py` | `build_network_status(target_lookup=…)` |
| `src/mycelium_admin/server.py` | `GET /status?lookup=<json>` |
| `tests/test_admin_daemon.py` | `test_status_lookup_map_single_match` |
| Gate doc Check 0c-vi | Split entity inspect vs query manual steps |

## Panel behavior

| Panel | Action | Wire |
|-------|--------|------|
| **Entity lookup** | **Inspect** | `GET /status` with `entity` or `lookup` — no `POST /query` |
| **Run query** | Step 1 **Run** | `POST /query` with `id` or `lookup` only |
| **Run query** | Step 2 **Deliver** | `POST /query` with `delivery_id` (+ optional `quote_id`) |

Both panels share the same resolve form state (mode, ID, MVR bind fields). `confirm_new_entity` remains lookup step-1 only (1220 behavior).

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 405 passed, 26 deselected
```

Manual:

```bash
./bin/restart-admin crm
# Entity lookup → Andrea by name → Inspect → drill-down (no POST /query in DevTools)
# Run query → Step 1 Run in step-1 fieldset; Step 2 Deliver separate
```

## For Grok + Paul

- **Inspect restored** — browse-only `GET /status` path works again without merging into query.
- **Layout** — radios clearly scope stacked inputs below; attributes/Run separated from deliver row.
- **Gate doc** — Check 0c-vi split into entity inspect + run query sections.
- **Not committed** — awaiting review.

Suggested commit message:

```
fix(admin-ui): restore entity inspect panel and split query step buttons

Two panels share identical resolve form; Inspect uses GET /status with lookup
map; query has separate Step 1 Run and Step 2 Deliver; layout cleanup.
```

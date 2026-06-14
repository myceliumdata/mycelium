# Admin UI — unified query & entity lookup with dynamic MVR fields

## Summary

Merged **Run query** and **Entity lookup** into a single **Query & entity lookup** panel. Step 1 now supports mutually exclusive **Registry ID** or **dynamic MVR lookup** fields driven by `capabilities.policy.mvr.bind_fields`. Step-1 resolution uses `POST /query`; entity drill-down refreshes via `GET /status` after each step-1 run.

## Changes

| Area | Change |
|------|--------|
| `admin-ui/src/App.tsx` | Unified panel; step-1/step-2 fieldsets; mode radio; dynamic bind inputs; drill-down below results |
| `admin-ui/src/mvr.ts` | New helpers: `mvrBindFieldsFromPolicy`, `buildLookupPayload`, `statusEntityKeyForResolve`, `lookupFromSuggestion` |
| `admin-ui/src/types.ts` | `MvrPolicy` typing on capabilities |
| `admin-ui/src/styles.css` | Fieldset, mode radio, lookup fields, drill-down border styles |
| `docs/manual-checks/...-gate.md` | Check 0c-vi panel label → **Query & entity lookup** |

## UI behavior

- **Step 1 — resolve:** Registry ID (`{ id }`) **or** MVR lookup (`{ lookup }`) — radio toggle clears the other mode.
- **Bind fields:** Read from `/capabilities` → `policy.mvr.bind_fields`; fallback `name, employer` while loading.
- **Step 2 — deliver:** `delivery_id` + optional `quote_id`; when `delivery_id` is set, step-1 fields are disabled.
- **Drill-down:** After step-1 `POST /query`, status refresh uses derived entity key (UUID in ID mode; `lookup.name` or first non-empty bind value in lookup mode).
- **Suggestions:** Click populates dynamic bind fields, switches to MVR lookup mode, clears confirm flag.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 403 passed, 26 deselected
```

Manual:

```bash
./bin/restart-admin crm
# http://127.0.0.1:8741/ → Query & entity lookup
# - MVR mode shows name + employer inputs from policy
# - Registry ID mode + Andrea UUID → lookup_resolved + drill-down
# - Name only → lookup_incomplete + required_fields
# - Andrea @ Wrong Corp → lookup_suggested + confirm checkbox
```

## For Grok + Paul

- **bind_fields source confirmed:** `mvrBindFieldsFromPolicy()` reads `capabilities.policy.mvr.bind_fields` from `build_network_capabilities()` (same as `describe_network`).
- **Gate doc:** Check 0c-vi updated to reference unified panel name.
- **No backend changes** — `POST /query` already accepts `id`.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat(admin-ui): unify query lookup with dynamic MVR fields and ID resolve

Merge query and entity lookup panels; step-1 id OR dynamic MVR lookup from
policy.mvr.bind_fields; target-protocol POST /query with status drill-down.
```

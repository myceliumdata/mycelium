# Review: 2026-06-14-1200-admin-query-unified-mvr-lookup

**Verdict: Approved + fix slice**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 403 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 403 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| `admin-ui/src/App.tsx` — unified panel | ✅ |
| `admin-ui/src/mvr.ts` — dynamic MVR helpers | ✅ |
| `admin-ui/src/types.ts` — `MvrPolicy` typing | ✅ |
| `admin-ui/src/styles.css` — fieldset / drill-down styles | ✅ |
| Gate doc Check 0c-vi label update | ✅ |
| `output.md` / `prompt.md` | ✅ |

## Diff reviewed

- `admin-ui/src/App.tsx`
- `admin-ui/src/mvr.ts`
- `admin-ui/src/types.ts`
- `admin-ui/src/styles.css`
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Single panel replaces duplicate forms | ✅ |
| Step 1: registry ID or MVR lookup — mutually exclusive | ✅ |
| Lookup inputs from `policy.mvr.bind_fields` | ✅ |
| Step 1 uses `POST /query`; drill-down uses `GET /status` | ✅ |
| Suggestions populate dynamic bind fields | ✅ |
| `./bin/ci-local` green | ✅ |
| `confirm_new_entity` checkbox in UI | ✅ UI only — **admin API does not wire field** (see below) |

## Legacy / dual-path

- Drill-down still shows legacy `status.entity_suggestions` / `entity_required_fields` from `GET /status` (harmless redundancy alongside query-result fields).
- Target protocol used for step-1 resolution as required.

## Tests

No new automated tests (UI-only slice per prompt). Manual Check 0c-vi paths covered in `output.md`.

## Design critique

**Strong:** Clean `mvr.ts` extraction; `bindFields` synced via `useEffect`; step-1 fieldset disabled when `delivery_id` set; mode toggle clears opposing values; gate doc updated.

**Blocking (fix slice):** `AdminQueryRequest` in `src/mycelium_admin/server.py` does **not** include `confirm_new_entity`, and `EntityQuery(...)` construction omits it. UI sends the field but admin daemon drops it — **Confirm new entity checkbox has no effect** in admin (Check 0c-iv manual step). Wire field + smoke test `POST /query` with `confirm_new_entity: true`.

**Non-blocking:**

- UI sends `confirm_new_entity` on **id** mode too (line 447); backend rejects if ever wired while checkbox stale after mode switch. Should only attach in lookup mode.
- Duplicate suggestion lists (query result vs status drill-down) — could hide status suggestions when `queryResult` already has suggestions.

## Nits

| Severity | Item |
|----------|------|
| **Blocking** | Admin `POST /query`: add `confirm_new_entity` to `AdminQueryRequest` + `EntityQuery` construction; test in `test_admin_daemon.py`. |
| Non-blocking | Omit `confirm_new_entity` from request body when `resolveMode === "id"`. |
| Non-blocking | Hide drill-down `status.entity_suggestions` when `queryResult.suggestions` non-empty. |

## For Paul

**Commit message:**

```
feat(admin-ui): unify query lookup with dynamic MVR fields and ID resolve

Merge query and entity lookup panels; step-1 id OR dynamic MVR lookup from
policy.mvr.bind_fields; target-protocol POST /query with status drill-down.
```

**Next:** Queue small fix slice for admin `confirm_new_entity` wire before relying on Check 0c-iv checkbox in admin UI.

**Manual:** `./bin/restart-admin crm` → **Query & entity lookup** panel.
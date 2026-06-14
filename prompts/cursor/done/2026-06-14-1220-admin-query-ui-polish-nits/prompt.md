# Admin UI polish — confirm_new_entity scope + dedupe suggestions

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context:** Grok review of slice `1200-admin-query-unified-mvr-lookup` ([`review.md`](../done/2026-06-14-1200-admin-query-unified-mvr-lookup/review.md)) logged two **non-blocking** UI nits. Slice `1215` wires `confirm_new_entity` on the admin daemon; this slice fixes the admin **UI** behavior around that flag and duplicate suggestion lists.

**Prerequisites:** `1200` on `main`. Prefer starting after `1215` lands (confirm wire), but changes here are UI-only and do not depend on backend edits.

---

## Tasks (both required)

### 1. `confirm_new_entity` — lookup mode only

In `admin-ui/src/App.tsx` `runQueryRequest`:

- Send `confirm_new_entity` **only** when `resolveMode === "lookup"` (MVR lookup step 1).
- **Do not** include `confirm_new_entity` in the JSON body for:
  - `resolveMode === "id"` (registry ID step 1)
  - step 2 (`delivery_id` present)

**Also:** When user switches to **Registry ID** mode (`onResolveModeChange("id")`), clear `queryConfirmNewEntity` to `false` so a stale checkbox cannot leak into a later id resolve after `1215` wires the backend.

`EntityQuery` rejects `confirm_new_entity` with id-only step 1 (`confirm_new_entity applies to lookup create path only`).

### 2. Dedupe suggestion lists in drill-down

In the **entity drill-down** section (below query results in the unified panel):

- **Hide** `status.entity_suggestions` when `queryResult` already has non-empty `suggestions` from the latest `POST /query`.
- Query-result suggestions remain the primary list (target protocol, with `reason` values like `same_name_different_employer`).
- When there is no `queryResult` or `queryResult.suggestions` is empty, legacy `status.entity_suggestions` may still render (status-only drill-down path).

Optional consistency: apply the same rule to `status.entity_required_fields` when `queryResult.required_fields` is non-empty — only if trivial; not required for this slice.

---

## Read first

- `admin-ui/src/App.tsx` — `runQueryRequest`, `onResolveModeChange`, drill-down block (~`status.entity_suggestions`)
- `prompts/cursor/done/2026-06-14-1200-admin-query-unified-mvr-lookup/review.md` — nits table

---

## Scope boundaries

**May modify:**

- `admin-ui/src/App.tsx` only

**Out of scope:**

- `src/mycelium_admin/server.py` (1215)
- `TODO.md`
- New automated tests (manual verify sufficient)

---

## Verification

```bash
./bin/ci-local
./bin/restart-admin crm
```

Manual:

1. **Lookup suggested** → Andrea @ Wrong Corp → suggestions in query result; drill-down does **not** repeat a second suggestion list.
2. **Confirm checkbox** → check it → switch radio to **Registry ID** → checkbox clears; Run with UUID does not send `confirm_new_entity` (DevTools Network tab on `POST /query` body).
3. **Registry ID** resolve still works without confirm in body.

---

## Governance

- Do not edit `TODO.md`.
- `output.md` → **For Grok + Paul**: note both nits addressed.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1220-admin-query-ui-polish-nits/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- `confirm_new_entity` omitted for id mode and step 2; cleared on switch to id mode
- Drill-down hides duplicate `status.entity_suggestions` when query suggestions present
- `./bin/ci-local` green

Suggested commit message:

```
polish(admin-ui): scope confirm_new_entity to lookup and dedupe suggestions

Send confirm flag only on MVR lookup step 1; clear on id mode switch;
hide legacy status suggestions when query result already has suggestions.
```
# Admin UI polish — confirm_new_entity scope + dedupe suggestions

## Summary

Addressed two non-blocking review nits from slice `1200`: scoped `confirm_new_entity` to MVR lookup step 1 only, and hid duplicate suggestion/required-field lists in the entity drill-down when query results already carry them.

## Changes

| Nit | Fix |
|-----|-----|
| `confirm_new_entity` sent on id resolve | Omitted from registry ID and step-2 bodies; only included on MVR lookup step 1 |
| Stale confirm after mode switch | Cleared `queryConfirmNewEntity` when switching to Registry ID mode |
| Duplicate suggestion lists | Drill-down hides `status.entity_suggestions` when `queryResult.suggestions` is non-empty |
| Duplicate required fields (bonus) | Drill-down hides `status.entity_required_fields` when `queryResult.required_fields` is non-empty |

**File:** `admin-ui/src/App.tsx` only.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 404 passed, 26 deselected
```

Manual (`./bin/restart-admin crm`):

1. Andrea @ Wrong Corp → suggestions appear once (query result only).
2. Check confirm → switch to Registry ID → checkbox clears; `POST /query` body has no `confirm_new_entity`.
3. Registry ID resolve still works.

## For Grok + Paul

- Both review nits from `1200` review addressed.
- No backend changes.
- **Not committed** — awaiting review.

Suggested commit message:

```
polish(admin-ui): scope confirm_new_entity to lookup and dedupe suggestions

Send confirm flag only on MVR lookup step 1; clear on id mode switch;
hide legacy status suggestions when query result already has suggestions.
```

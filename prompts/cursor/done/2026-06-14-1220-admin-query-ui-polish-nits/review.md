# Review: 2026-06-14-1220-admin-query-ui-polish-nits

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 404 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 404 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| `confirm_new_entity` lookup-only in `runQueryRequest` | ✅ |
| Clear confirm on switch to Registry ID | ✅ |
| Dedupe `status.entity_suggestions` | ✅ |
| Bonus: dedupe `status.entity_required_fields` | ✅ |
| `output.md` / `prompt.md` | ✅ |

## Diff reviewed

- `admin-ui/src/App.tsx`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| `confirm_new_entity` omitted for id mode and step 2 | ✅ (id fixed; step 2 never sent it) |
| Cleared on switch to id mode | ✅ |
| Drill-down hides duplicate status suggestions | ✅ |
| `./bin/ci-local` green | ✅ |

## Tests

UI-only slice; manual verification documented in `output.md`. No new automated tests required.

## Design critique

**Strong:** Small, focused diff; `showStatusSuggestions` / `showStatusRequiredFields` flags are clear. Bonus required-fields dedupe improves the same UX issue without scope creep.

**Nits:** None.

## For Paul

**Commit message:**

```
polish(admin-ui): scope confirm_new_entity to lookup and dedupe suggestions

Send confirm flag only on MVR lookup step 1; clear on id mode switch;
hide legacy status suggestions when query result already has suggestions.
```

**Queue:** Empty — next slice TBD.
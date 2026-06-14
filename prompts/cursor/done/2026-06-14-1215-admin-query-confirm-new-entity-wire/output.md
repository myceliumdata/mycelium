# Admin daemon — wire confirm_new_entity on POST /query

## Summary

The admin UI checkbox for `confirm_new_entity` was inert because `AdminQueryRequest` did not accept or forward the field. This slice wires it through to `EntityQuery` on `POST /query`.

## Changes

| Area | Change |
|------|--------|
| `src/mycelium_admin/server.py` | `confirm_new_entity: bool = False` on `AdminQueryRequest`; passed to `EntityQuery` |
| `tests/test_admin_daemon.py` | `test_admin_query_confirm_new_entity_creates` — suggested → confirmed create |

## Test coverage

1. Andrea @ Wrong Corp → `lookup_suggested`
2. Same lookup + `confirm_new_entity: true` → `lookup_resolved`, `delivery.create_on_deliver: true`

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 404 passed, 26 deselected
```

## For Grok + Paul

- **UI unchanged** — checkbox from slice `1200` now works end-to-end via admin daemon.
- **Not committed** — awaiting review.

Suggested commit message:

```
fix(admin): wire confirm_new_entity through POST /query

Forward confirm_new_entity from AdminQueryRequest to EntityQuery so the
admin UI checkbox can create after lookup_suggested.
```

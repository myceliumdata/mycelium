# Admin daemon — wire confirm_new_entity on POST /query

> **READY** — Move to `in-progress/` before starting.

**Context:** Slice `1200-admin-query-unified-mvr-lookup` added admin UI checkbox for `confirm_new_entity`, but `AdminQueryRequest` / `EntityQuery` construction in `src/mycelium_admin/server.py` never forwards the field. Checkbox is inert.

**Prerequisites:** `1200` admin UI slice committed.

---

## Task

1. Add `confirm_new_entity: bool = False` to `AdminQueryRequest`.
2. Pass through to `EntityQuery(confirm_new_entity=body.confirm_new_entity)` in `POST /query`.
3. Smoke test in `tests/test_admin_daemon.py`:
   - Andrea @ Wrong Corp → `lookup_suggested`
   - Same body + `confirm_new_entity: true` → `lookup_resolved`, `delivery.create_on_deliver: true`

**Out of scope:** UI changes (already done).

---

## Verification

```bash
./bin/ci-local
```

Do not commit or push. Tell Paul **slice ready for review**.
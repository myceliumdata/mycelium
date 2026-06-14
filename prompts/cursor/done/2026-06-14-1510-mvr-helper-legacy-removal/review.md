# Review — Slice 1510: MVR helper legacy removal (item 5)

**Verdict:** ✅ **Approved**

**Reviewer:** Grok  
**Date:** 2026-06-14  
**CI:** `./bin/ci-local` green — **424 passed**, 26 deselected

---

## Scope check

| Requirement | Status |
|-------------|--------|
| Remove `required_bind_fields(entity_key, binding)` | ✅ |
| Remove `required_fields_for_entity_key` | ✅ |
| Remove `allowed_binding_keys` / `normalize_binding` | ✅ |
| Single rule: `missing_mvr_bind_fields(lookup)` | ✅ |
| Legacy callers bridged via `legacy_entity_lookup_map` until 1530 | ✅ |
| New smokes: partial name, employer-only, policy has no legacy methods | ✅ |
| No `TODO.md` edit | ✅ |

---

## What looks good

- **`test_missing_mvr_bind_fields_employer_only`** proves the old bug is gone: `{"employer":"Acme"}` now correctly requires `name` (legacy rule would have treated a non-empty string as satisfying name only when it was `entity_key`, not when employer-only lookup).
- `legacy_entity_lookup_map` is an explicit, documented bridge — maps legacy inputs to a lookup dict before `missing_mvr_bind_fields`, rather than hiding satisfaction inside `MvrPolicy`.
- Grep clean: no remaining `required_bind_fields` / `normalize_binding` in `src/`.

---

## Polish backlog (1560)

| Item | Status after 1510 |
|------|-------------------|
| **P2** (`ensure_entity_bind_fields` requires `name`) | **Still open** — `attribute_write.py` unchanged; 1510 scoped to `mvr.py` + legacy resolution callers only |
| **P1, P3, P4** | Unchanged — still 1560 |

No new nits from this slice.

---

## CI

```
./bin/ci-local — all steps passed
424 passed, 26 deselected
```

---

## Commit

```
refactor(mvr): drop entity_key satisfaction from bind field helpers
```

**Next slice:** `1520-status-surfaces-target`.
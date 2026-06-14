# Review — Slice 1500: Generic registry bind_values + bind_index

**Verdict:** ✅ **Approved + polish nits**

**Reviewer:** Grok  
**Date:** 2026-06-14  
**CI:** `./bin/ci-local` green — **421 passed**, 26 deselected

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `bind_values` on disk; no top-level `name`/`employer` in JSON | ✅ `test_registry_entity_json_omits_top_level_name_employer` |
| Generic `make_bind_key(bind_values, bind_fields)` | ✅ `test_make_bind_key_respects_bind_fields_order` |
| `attribute_write` / `field_index` use `bind_values` | ✅ |
| `registry_entity_to_match` flat name/employer from cache | ✅ |
| `lookup_by_bind_key` wrapper for legacy until 1530 | ✅ per plan |
| Smoke tests + capstone bind_index tests | ✅ |
| No `TODO.md` edit | ✅ |

---

## What looks good

- Clean separation: canonical storage is `bind_values`; graph/response flat fields are derived.
- `write_bind_fields` index replace uses full MVR field snapshot via `_cache_values(entity, mvr)`.
- `promote_validated` field_states now driven by `mvr.bind_fields`.
- `target_resolve` employer normalization aligned with `field_index` (removed duplicate normalizer).
- Fixture updates in admin/provenance/growth tests match on-disk shape.

---

## Polish nits (non-blocking)

| # | Nit | Suggested follow-up |
|---|-----|---------------------|
| N1 | `RegistryEntity.name` / `.employer` **properties** — Paul locked **Option A** (map-only on disk). Properties are fine for transition but add CRM-flavored accessors; prefer `bind_value("name")` in new code. | **P1** → slice **1560** ([`entity-protocol-legacy-cleanup-polish.md`](../../../docs/plans/entity-protocol-legacy-cleanup-polish.md)) |
| N2 | `ensure_entity_bind_fields` still **`require lookup.name`** — CRM-specific gate not replaced by “all `mvr.bind_fields` present” policy. | **P2** → verify in **1510**; else **1560** |
| N3 | **No fail-loud load** for legacy rows with top-level `name`/`employer` (Pydantic ignores extras → empty `bind_values`). `output.md` documents refresh cutover; operators who skip refresh get silent breakage. | **P3** → slice **1560** |
| N4 | `lookup_by_bind_values` with **partial** `bind_values` pads missing bind fields as `""` in `make_bind_key` — acceptable while binds always pass full CRM pairs; document when generic 3+ field networks land. | **P4** → slice **1560** |

---

## CI

```
./bin/ci-local — all steps passed
421 passed, 26 deselected
```

Full integration (`pytest -m full`) not required — not program final slice.

---

## Commit

```
feat(registry): generic bind_values and bind_index for MVR fields
```

**Breaking:** refresh live networks after pull (`./bin/refresh-example-network crm --yes`).

**Next slice:** `1510-mvr-helper-legacy-removal` (queued). **Polish nits:** `1560-program3-polish`.
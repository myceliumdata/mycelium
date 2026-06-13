# Review — Program 2 Slice 1 (unified MVR bind write)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-13  
**CI (Grok):** `./bin/ci-local` — **373 passed**, 26 deselected; ruff clean; admin-ui build ok.

---

## Scope vs spec

| Requirement | Status |
|-------------|--------|
| Unified write API (`attribute_write.py`) | ✅ |
| Taxonomy ownership via `attribute_map` (fail loud) | ✅ `resolve_attribute_owner` |
| No `bind_versions[]` on entity row | ✅ |
| Route seed / registry bind / create-on-deliver | ✅ |
| `bind_index` replace on correction | ✅ tested |
| Field indexes maintained (MVR M4) | ✅ via `save_entity` → `_rebuild_field_indexes` |
| Sample categories + `attribute_map` for name/employer | ✅ |
| Out of scope: query provenance bind, admin bind timeline, research deference | ✅ untouched (one provenance test env fix only) |

---

## Diff reviewed (full)

**New:** `src/agents/attribute_write.py`, `src/network/category_mvr_bootstrap.py`, `tests/test_attribute_write.py`, `prompts/cursor/done/.../`

**Modified:** `entity_registry.py`, `target_deliver.py`, `seed_import.py`, `create.py`, `specialists/base.py`, `introspection.py`, `network_helpers.py`, `sample-categories.json`, docs, 6 test files.

---

## What works well

1. **Clear separation** — specialist `versions[]` for canonical bind values; registry row for cache + indexes. Matches locked Program 2 decisions.
2. **`resolve_attribute_owner`** uses classification tree only — no runtime hardcoded CRM map in the write path.
3. **`category_mvr_bootstrap`** solves the real failure mode Cursor hit: seed import before `categories.json` existed. Refresh/create paths now materialize or merge MVR mappings before bind writes.
4. **Tests** — focused `test_attribute_write.py` plus realistic updates to status/example tests reflecting “seed import now creates ontology + specialist storage rows.”
5. **`status_to_dict` JSON round-trip** — legitimate fix (tuples → lists) for admin/CLI JSON parity.

---

## Nits (non-blocking — log for Slice 3 / polish)

| # | Finding | Suggestion |
|---|---------|------------|
| N1 | **Multi-specialist writes not atomic** — `write_bind_fields` saves demographic then professional storage separately; crash between could split name/employer. | Accept for CRM v1; Slice 3 or polish: single-transaction note or rollback wrapper. |
| N2 | **`CRM_MVR_FIELD_CATEGORY` hardcoded** in `category_mvr_bootstrap.py` for merge/bootstrap only. Runtime resolve is taxonomy-clean; document that bootstrap defaults are CRM reference until `network create` LLM ontology includes custom bind→category maps. | Comment in module + program spec footnote. |
| N3 | **`_apply_cache_field` / `RegistryEntity`** only cache `name` and `employer` — arbitrary future `mvr.bind_fields` won’t denormalize on entity row until schema grows. | Expected; Slice 3 “dynamic bind fields” should call this out. |
| N4 | **Duplicate bind short-circuit** — `ensure_entity_bind_fields` returns existing row without backfilling specialist `versions[]`. Pre–Program 2 registry rows stay registry-only on duplicate hit. | OK per hard-cutover (refresh); mention in operator notes. |
| N5 | **`write_bind_fields` always appends** a new version even if value unchanged. | Low priority; operator/re-bind edge case. |
| N6 | **Docs say “Slice 1 shipped”** in `attribute-provenance-and-storage.md` before merge — wording is fine post-commit. | — |

---

## Behavioral change (operators)

**`./bin/refresh-example-network crm`** with `seed.json` now also writes **`categories.json`** (from sample or merge) and **`agents/demographic` + `agents/professional` storage** with versioned name/employer per seeded person. Status demo will show ontology ✅ and specialist counts for demographic/professional — tests updated accordingly. This is **correct** for Program 2, not accidental scope creep.

---

## Locked decisions check

| Decision | Honored? |
|----------|----------|
| No entity-level history | ✅ |
| Taxonomy ownership | ✅ (resolve); bootstrap uses CRM merge helper |
| Research vs operator | N/A this slice |
| Index replace, no aliases | ✅ bind_index; field indexes rebuilt on save |

---

## Next steps

1. **Grok or Paul:** commit with suggested message from `output.md` when ready.
2. **Queue Slice 2** after commit — provenance + admin bind field versions.
3. Optional: append N1–N2 to Program 2 polish / Slice 3 spec.

**Do not queue Slice 2 until this slice is committed and Paul signs off.**
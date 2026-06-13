# Program 2 — Slice 1: Unified MVR bind write API

## Summary

Introduced a unified attribute write path for MVR bind fields (`name`, `employer`). Canonical `versions[]` live in taxonomy-owned specialist storage; `entities.json` keeps cache columns, protocol fields, and derived indexes only. Seed bootstrap, registry bind, and create-on-deliver now route through the same API.

Added `category_mvr_bootstrap` so seed import and network create materialize or merge MVR field mappings in `categories.json` before bind writes run.

**Locked decisions honored:** no `bind_versions[]` on entity rows; owner resolution via `categories.json` `attribute_map` (fail loud when unmapped); index replace on bind correction.

## Changes

| Area | Change |
|------|--------|
| **`src/agents/attribute_write.py`** (new) | `resolve_attribute_owner`, `write_bind_fields`, `ensure_entity_bind_fields`, `ensure_entity_bind` |
| **`src/agents/entity_registry.py`** | `ensure_bound_entity` delegates to unified write; `register_entity`, `save_entity`, `assign_bind_index`, `pop_bind_index` |
| **`src/agents/target_deliver.py`** | `bind_provisional_from_scope` uses `ensure_entity_bind_fields` |
| **`src/network/seed_import.py`** | Bootstrap ensures categories before import |
| **`src/network/category_mvr_bootstrap.py`** (new) | Sample copy, merge MVR fields into existing ontology, `ensure_mvr_fields_in_category_tree` |
| **`src/network/create.py`** | Categories written before seed bootstrap; MVR fields merged into LLM ontology |
| **`docs/examples/sample-categories.json`** | `name` → demographic, `employer` → professional in `attribute_map` + examples |
| **`src/agents/specialists/base.py`** | Storage strategy notes: `bind_field_ownership: taxonomy` |
| **`src/network/introspection.py`** | `status_to_dict` JSON-safe (lists not tuples) |
| **`tests/test_attribute_write.py`** (new) | 7 tests: bind versions, cache, indexes, replace, unmapped error, integration smoke |
| **`tests/network_helpers.py`** | `apply_network_paths` before seed import |
| **Fixture / status tests** | Seed-only networks now show ontology + demographic/professional specialist counts after bootstrap |
| **Docs** | `architecture.md` Program 2 note; `attribute-provenance-and-storage.md` Slice 1 shipped |

## Bind version shape (seed / bind / create)

```json
{
  "id": "v1",
  "at": "2026-06-13T…",
  "status": "found",
  "value": "Andrea Kalmans",
  "actor": {
    "kind": "seed_bootstrap",
    "category": "demographic",
    "specialist": "demographic_specialist"
  }
}
```

Actor kinds: `bind`, `seed_bootstrap`.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 373 passed, 26 deselected
```

## For Grok + Paul

- **Slice complete** — unified MVR bind write API; seed/registry/create-on-deliver share one path.
- **Hands-on:** Refresh CRM example → `categories.json` auto-materialized; seed import writes `versions[]` under `agents/demographic` and `agents/professional`; entity row cache matches; `bind_index` + field indexes update on bind/replace.
- **Out of scope (Slice 2+):** query provenance bind inclusion, admin version UI, research operator deference.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: unified MVR bind write API with taxonomy-owned specialist storage

Add attribute_write module; route seed/registry/create-on-deliver binds through
one path; bootstrap categories.json for MVR attribute_map; entity row cache
+ indexes only (no bind_versions[]).
```

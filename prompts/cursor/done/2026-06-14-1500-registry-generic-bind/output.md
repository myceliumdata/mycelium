# Program 3 — Slice 1500: Generic registry bind_values + bind_index

## Summary

Registry rows on disk now store MVR bind fields in **`bind_values`** only (no top-level `name`/`employer`). `bind_index` keys are built generically from `mvr.bind_fields` via `make_bind_key(bind_values, bind_fields)`.

## Changes

| Area | Change |
|------|--------|
| `src/agents/entity_registry.py` | `RegistryEntity.bind_values`; `bind_value()` helper; `name`/`employer` properties (internal, not serialized); generic `make_bind_key`, `lookup_by_bind_values`, `assign_bind_index`/`pop_bind_index` |
| `src/agents/attribute_write.py` | Writes/read snapshots via `bind_values`; index updates use generic keys |
| `src/agents/field_index.py` | Reads bind fields from `bind_values` only |
| `src/agents/target_resolve.py` | Uses `normalize_field_index_value` for employer comparison |
| Tests | `bind_values` JSON assertions; `test_registry_entity_json_omits_top_level_name_employer`; `test_make_bind_key_respects_bind_fields_order`; fixture updates |

## Design notes

- **`registry_entity_to_match`** still returns flat `name`/`employer` derived from `bind_values` for graph/response builders.
- **`lookup_by_bind_key(name, employer)`** retained as thin CRM wrapper for legacy `entity_key` path until slice 1530.
- **Seed import** unchanged at `seed.json` shape; maps to `bind_values` on write.
- **Hard cutover** — no migration from old top-level `name`/`employer` columns.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 421 passed, 26 deselected
```

## For Grok + Paul

- Slice **1500** complete — update [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md) status after review.
- **Breaking:** existing `entities.json` with top-level `name`/`employer` must be refreshed (`./bin/refresh-example-network crm --yes`) before use.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat(registry): generic bind_values and bind_index for MVR fields
```

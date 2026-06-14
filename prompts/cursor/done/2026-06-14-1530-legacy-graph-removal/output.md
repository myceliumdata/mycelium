# Program 3 — Slice 1530: Legacy graph and resolution removal

## Summary

Removed the deprecated `entity_key` + `binding` query graph path. Step-1 inputs are now **`id`** and **`lookup`** only; legacy resolution helpers and outcome builders are gone.

## Production changes

| Area | Change |
|------|--------|
| `EntityQuery` | Removed `entity_key` / `binding`; `extra="forbid"`; step 1 requires `id` or `lookup` |
| `entity_resolution.py` | Removed `resolve_entity`, `resolve_entity_key`, `resolve_entity_for_lookup`, `lookup_entities_by_key`; kept target helpers + fuzzy rankers |
| `entity_registry.py` | Replaced `lookup_by_name` with `lookup_by_field` |
| `mvr.py` | Removed `legacy_entity_lookup_map` |
| `supervisor.py` | Deliver-only coordinator (no `resolve_entity` path) |
| `dispatch.py` | Removed legacy deferral + legacy assemble branches |
| `responses.py` | Removed legacy outcome builders; updated `debug_for_query` |
| `routing.py` | **Deleted** (test-only shim) |
| Specialists + template | Error paths use `current.current_id` |
| Admin UI | Removed `entity_validated` success badge handling |

## Tests

| Change | Detail |
|--------|--------|
| **New** `test_entity_query_rejects_entity_key_field` | Model rejects `entity_key` |
| **New** `test_entity_query_rejects_binding_field` | Model rejects `binding` |
| **New** `test_supervisor_no_legacy_entity_key_path` | ValidationError + target lookup still works |
| **Removed** legacy env-flag test | `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` dropped from conftest |
| **Deferred** 17 legacy test modules | `pytest_ignore_collect` → slice **1540** |
| **Added** `tests/registry_helpers.py` | Fixture name lookups via `lookup_by_field` |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 288 passed, 13 deselected
```

## For Grok + Paul

- Slice **1540** must migrate/deleted the 17 ignored `entity_key` test modules.
- `describe_network` policy strings still mention legacy outcomes (slice **1550**).
- **Committed** after Grok review (see `review.md`).

Suggested commit message:

```
refactor(query): remove legacy entity_key graph and resolution path
```

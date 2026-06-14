# Program 3 — Slice 1560: Polish (review nits)

## Summary

Closed P1–P4 registry/bind_values nits from Program 3 slice reviews. Program 3 polish complete.

## P1 — Remove `RegistryEntity.name` / `.employer` properties

- Deleted `@property` accessors on `RegistryEntity`
- Migrated callers to `bind_value("name")` / `bind_value("employer")`:
  - `registry_entity_to_match`, `dispatch.py`, `target_resolve.py`, `entity_resolution.py`
- Tests updated to `bind_value()` assertions

## P2 — Full MVR bind policy (`ensure_entity_bind_fields`)

- Replaced `require lookup.name` with `require_full_bind_values(values, mvr.bind_fields)`
- **Test:** `test_ensure_entity_bind_fields_requires_all_mvr_fields`
- Seed import validates employer present (`seed_import.py` clear error message)
- Test fixtures updated with employer in seed rows

## P3 — Fail-loud legacy `entities.json` load

- Added `LegacyEntitiesSchemaError` + `_reject_legacy_entity_rows()` in `_load`
- Propagates (not swallowed) when top-level `name`/`employer` without `bind_values`
- **Test:** `test_legacy_entities_json_load_fails_loud`

## P4 — Full MVR `bind_values` for bind_index

- Added `require_full_bind_values()` — no silent `""` padding
- `make_bind_key`, `lookup_by_bind_values`, `assign_bind_index`, `pop_bind_index` use it
- `_cache_values` requires full bind on entity
- `write_bind_fields` skips old bind_index pop when entity has no prior full bind (first write)
- **Tests:** `test_make_bind_key_partial_bind_values_raises`, `test_lookup_by_bind_values_requires_full_mvr`

## P5–P9 — Waived / closed

| # | Status |
|---|--------|
| P5 | **Waived** — none (1510 review) |
| P6 | **Waived** — none (1520 review) |
| P7 | **Closed** in 1540 (conftest legacy block removed) |
| P8 | **Waived** — none (1540 review) |
| P9 | **Waived** — none (1550 review) |

## Test updates

- `test_network_create.py` — seed fixtures include `employer` (full MVR)
- `test_network_status.py` — `test_status_bind_rows_include_empty_employer` uses direct registry row (no bind_index) for synthetic missing-employer display

## Docs

- `entity-protocol-legacy-cleanup-polish.md` — exit criteria checked
- `entity-protocol-legacy-cleanup-program.md` — polish slice complete

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 405 passed, 26 deselected
```

## For Grok + Paul

- **Program 3 fully complete** (code + polish)
- Grok: run `pytest -m full` at review per WORKFLOW
- Suggested commit:

```
chore(program3): polish registry bind_values and load hardening nits
```

- **Committed** after Grok review (see `review.md`).

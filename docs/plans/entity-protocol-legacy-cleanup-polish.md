# Program 3 — Polish backlog (post Slice 1550)

**Status:** **Complete** — polish slice 1560 (June 2026)  
**Cursor prompt:** `prompts/cursor/next/2026-06-14-1560-program3-polish.md`  
**Program:** [`entity-protocol-legacy-cleanup-program.md`](entity-protocol-legacy-cleanup-program.md)

---

## Purpose

Non-blocking nits from Grok review of Program 3 slices. One polish pass at program end — **do not** block 1510–1550; Grok appends rows here from each slice `review.md` before 1560 runs.

---

## Backlog

| # | Source | Nit | Polish action |
|---|--------|-----|----------------|
| P1 | 1500 review N1 | `RegistryEntity.name` / `.employer` **properties** — disk is `bind_values` only (Option A); properties keep CRM-flavored accessors alive | **Done** — properties removed; callers use `bind_value()` |
| P2 | 1500 review N2 | `ensure_entity_bind_fields` still **`require lookup.name`** | **Done** — `require_full_bind_values` for all `mvr.bind_fields`; `test_ensure_entity_bind_fields_requires_all_mvr_fields` |
| P3 | 1500 review N3 | Legacy `entities.json` rows with top-level `name`/`employer` load as empty `bind_values` (Pydantic ignores extras) | **Done** — `LegacyEntitiesSchemaError` in `_load`; `test_legacy_entities_json_load_fails_loud` |
| P4 | 1500 review N4 | `lookup_by_bind_values` / `make_bind_key` with **partial** `bind_values` pads missing fields as `""` | **Done** — `require_full_bind_values`; `test_make_bind_key_partial_bind_values_raises`, `test_lookup_by_bind_values_requires_full_mvr` |

### From later slices (Grok fills before 1560)

| # | Source | Nit | Polish action |
|---|--------|-----|----------------|
| P5 | 1510 review | *(none)* | — |
| P6 | 1520 review | *(none)* | — |
| P7 | 1530 review N1 | `conftest.py` redundant `pytest_collection_modifyitems` after `pytest_ignore_collect` | **Closed** in 1540 (legacy block removed) |
| P8 | 1540 review | *(none)* | — |
| P9 | 1550 review | *(none)* | — |

---

## Exit criteria

- [x] P1–P4 addressed (P2 verified or fixed)
- [x] P5–P9 addressed or marked **waived** in `output.md`
- [x] `./bin/ci-local` green
- [x] No Program 4 scope creep

---

*Last updated: 2026-06-14 (1560 polish complete)*
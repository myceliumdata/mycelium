# Program 3 — Polish backlog (post Slice 1550)

**Status:** Queued — run **after** slices 1500–1550  
**Cursor prompt:** `prompts/cursor/next/2026-06-14-1560-program3-polish.md`  
**Program:** [`entity-protocol-legacy-cleanup-program.md`](entity-protocol-legacy-cleanup-program.md)

---

## Purpose

Non-blocking nits from Grok review of Program 3 slices. One polish pass at program end — **do not** block 1510–1550; Grok appends rows here from each slice `review.md` before 1560 runs.

---

## Backlog

| # | Source | Nit | Polish action |
|---|--------|-----|----------------|
| P1 | 1500 review N1 | `RegistryEntity.name` / `.employer` **properties** — disk is `bind_values` only (Option A); properties keep CRM-flavored accessors alive | Remove properties; migrate internal callers to `bind_value("name")` / `bind_value("employer")` or explicit map reads |
| P2 | 1500 review N2 | `ensure_entity_bind_fields` still **`require lookup.name`** | **Still open** (1510 closed `mvr.py` helpers only) — require all `mvr.bind_fields` for new entity / bind_index key in `attribute_write.py` |
| P3 | 1500 review N3 | Legacy `entities.json` rows with top-level `name`/`employer` load as empty `bind_values` (Pydantic ignores extras) | Fail loud in `EntityRegistry._load` with actionable error (“refresh network” / invalid schema version) |
| P4 | 1500 review N4 | `lookup_by_bind_values` / `make_bind_key` with **partial** `bind_values` pads missing fields as `""` | Require full MVR `bind_values` for bind_index lookup/assign; raise `ValueError` if any `mvr.bind_fields` key missing or empty |

### From later slices (Grok fills before 1560)

| # | Source | Nit | Polish action |
|---|--------|-----|----------------|
| P5 | 1510 review | *(none)* | — |
| P6 | 1520 review | *(none)* | — |
| P7 | 1530 review N1 | `conftest.py` redundant `pytest_collection_modifyitems` after `pytest_ignore_collect` | **Closed** in 1540 (legacy block removed) |
| P8 | 1540 review | *(none)* | — |
| P9 | — | *(add from 1550 review)* | |

---

## Exit criteria

- [ ] P1–P4 addressed (P2 verified or fixed)
- [ ] P5–P9 addressed or marked **waived** in `output.md`
- [ ] `./bin/ci-local` green
- [ ] No Program 4 scope creep

---

*Last updated: 2026-06-14 (1540 review — P7 closed, P8 none)*
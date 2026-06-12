# Program 1 — Polish backlog (post Slice 3)

**Status:** Queued after Slice 3 review  
**Cursor prompt:** `prompts/cursor/next/2026-06-11-1400-attribute-provenance-slice-polish.md`  
**Program:** [`attribute-provenance-program1.md`](attribute-provenance-program1.md)

---

## Purpose

Non-blocking nits from Grok review of Slices 1–3. One polish pass after Program 1 ships — **do not** insert into the main slice sequence.

**Blocking nits** become fix slices immediately after the reviewed slice (see `prompts/cursor/WORKFLOW.md`).

---

## Backlog

| # | Source | Nit | Polish action |
|---|--------|-----|----------------|
| P1 | Slice 1 review | `ensure_versioned_for_write` silently wraps legacy flat **pending** into versioned `v1` | Document in `specialist_fields` docstring + architecture note; add smoke test asserting wrap behavior OR fail loud on flat pending (prefer **document + test** unless test proves wrap is required for retry gates) |
| P2 | Slice 1 review | `entity_growth` retains flat `researched_at` fallback | Remove flat branch; versioned-only attribution path |
| P3 | Slice 1 review | `_persist_field_version` duplicate `pending` branches | Delete dead duplicate branch |
| P4 | Slice 1 review | No explicit test for P1-11 in-place pending retry (`started_at` preserved) | Add smoke test: two `_write_pending` calls on same field → single `v1`, same `started_at`, updated `last_error` / `at` |
| P5 | Slice 1 review | `specialist_fields` read helpers still tolerate flat v1 (`current_value`, `field_has_value`, `current_status`) | After Slices 2–3, remove flat fallbacks; reads go through versioned path only (fail loud via `validate_versioned_field` at storage boundary) |
| P7 | Slice 2 review | `_analyze_storage` flat v1 fallback counting | Use versioned-only path or validate before count |
| P8 | Slice 2 review | No status/introspection smoke test for flat v1 fail loud on drill-down | Add smoke test on `build_network_status` / `/status` |
| P9 | Slice 2 review | `_entity_field_statuses` no-op empty-status branch | Remove dead branch |
| P10 | Slice 2 review | Admin `.version-history` unstyled | Add minimal CSS or use existing disclosure styles |
| P11 | Slice 3 review | `query_provenance._category_for_attribute` uses private `CategoryTree._data` | Public read-only category-for-attr helper or document |
| P12 | Slice 3 review | No multi-match `provenance.entities` smoke test | Add test with two registry ids + versioned storage |

---

## Exit criteria

- [ ] P1–P12 addressed
- [ ] `./bin/ci-local` green
- [ ] No new flat v1 read/write tolerance outside explicit tests for rejection behavior

---

*Last updated: June 2026 (Slice 1–3 review nits)*
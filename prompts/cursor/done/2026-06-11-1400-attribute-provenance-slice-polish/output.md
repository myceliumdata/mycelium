# Program 1 — Attribute provenance polish

## Summary

Closed review nits P1–P12 from Slices 1–3: versioned-only read paths, dead-code removal, tests, admin CSS, and public category lookup.

## Changes by nit

| # | Action |
|---|--------|
| **P1** | Documented `ensure_versioned_for_write` flat-pending wrap in docstring + `docs/architecture.md`; smoke test `test_ensure_versioned_for_write_wraps_flat_pending` |
| **P2** | Removed flat `researched_at` fallback from `entity_growth.py`; growth mock uses versioned fixtures |
| **P3** | Removed duplicate pending branch in `_persist_field_version` (`research.py`) |
| **P4** | Smoke test `test_write_pending_in_place_retry_preserves_started_at` |
| **P5** | Removed flat v1 fallbacks from `specialist_fields` read helpers; updated research/sync/integration tests to versioned fixtures |
| **P7** | `_analyze_storage` validates + counts versioned fields only |
| **P8** | Smoke test `test_status_flat_v1_field_fails_loud_on_drill_down` |
| **P9** | Removed no-op empty-status branch in `_entity_field_statuses` |
| **P10** | Styled admin `.version-history` in `admin-ui/src/styles.css` |
| **P11** | Added `CategoryTree.mapped_category()`; `query_provenance` uses public API |
| **P12** | Smoke test `test_build_query_provenance_multi_match_entities` |

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 296 smoke passed, 26 deselected
```

## For Grok + Paul

- **Program 1 polish complete** — all P1–P12 addressed; hard cutover reads enforced at storage boundary.
- **Program 1 complete** — Slices 1–3 + polish; ready for closeout review.
- **Program 2 design** may start after polish review.
- **Not committed** — awaiting review.

Suggested commit message:

```
chore: Program 1 provenance polish — versioned-only reads and review nits

Remove flat v1 read fallbacks, tighten introspection counts, add P1/P4/P8/P12
tests, style admin version history, public mapped_category helper.
```

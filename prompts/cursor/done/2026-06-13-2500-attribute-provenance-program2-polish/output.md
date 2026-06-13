# Program 2 — Polish (review nits P1–P7)

## Summary

Closed all non-blocking Grok review nits from Program 2 Slices 1–3 in one pass: research prompt ordering, shared specialist read helpers, no-op bind skip, multi-category write rollback, empty employer status rows, bootstrap docs, and hard-cutover note.

## P1–P7 checklist

| Nit | Status | Notes |
|-----|--------|-------|
| **P1** Research prompt block ordering | Done | `build_research_prompts` uses ordered `leading` list: disambiguation → operator → peer → category guidance → payload. Test: `test_build_research_prompts_block_order_disambig_operator_peer` |
| **P2** Shared specialist field version loader | Done | `specialist_fields.py`: `storage_record`, `field_versions_from_storage`, `version_tuple_from_entry`, `current_value_matches`. Refactored `query_provenance.py` and `introspection.py` |
| **P3** Skip no-op bind version append | Done | `current_value_matches` gate in `_apply_specialist_bind_writes`. Test: `test_write_bind_fields_skips_duplicate_version` |
| **P4** Multi-specialist write atomicity | Done | Snapshot + save-all + rollback on failure in `_apply_specialist_bind_writes`. Test: `test_write_bind_fields_rollback_on_second_save_failure` (asserts `records` equality; `last_updated` always refreshes on save) |
| **P5** Admin bind status for empty employer | Done | Removed empty employer skip in `_bind_field_statuses`. Test: `test_status_bind_rows_include_empty_employer` |
| **P6** Bootstrap CRM map documentation | Done | Module docstring in `category_mvr_bootstrap.py`; footnote in `attribute-provenance-program2.md` |
| **P7** Duplicate bind hard-cutover note | Done | Paragraph in `examples/networks/crm/README.md` |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 382 passed, 26 deselected
```

## For Grok + Paul

- **Polish complete** — Program 2 review nits P1–P7 closed; no Program 3 scope.
- **Hands-on:** Re-run bind with unchanged name → no duplicate version; failed multi-category write rolls back specialist `records`; admin status shows empty employer row; research prompts order operator before peer when all blocks present.
- **Program 2 fully shippable** after Grok review of this polish pass.
- **Not committed** — awaiting review.
- **TODO.md:** unchanged (per workflow).

Suggested commit message:

```
chore: close Program 2 polish nits P1–P7

Fix research prompt block order; share specialist version loaders; skip
no-op bind appends; rollback multi-category writes; show empty employer
in admin status; document bootstrap map and duplicate-bind cutover.
```

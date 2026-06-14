# Fix provisional validation on step-2 deliver (Q5a)

## Summary

Step-2 deliver now runs `validate_entity` for provisional registry rows — including identity-only deliver (no `requested_attributes`). Multi-match scopes validate and promote each provisional row independently; Q5b single-match failure path unchanged.

## Root cause

Identity-only step-2 preset `response` in `target_resolve_node` and skipped the graph before `validate_entity`. Multi-match step-2 with attrs hit `validate_entity` early return when `len(matched) != 1`.

## Changes

| Area | Change |
|------|--------|
| `src/agents/dispatch.py` | Identity-only step-2 with any provisional row routes through supervisor → validate → assemble; multi-match validation loop; delivery step skips `entity_validated` → returns `found` |
| `examples/networks/crm/README.md` | Step-2 validation applies to identity-only deliver |
| `tests/test_mvr_create_on_deliver.py` | Extended create-on-deliver test + `test_multi_match_step2_promotes_provisional_bind` |

## Batch validation policy (multi-match)

Each provisional row is validated independently. Rows that pass are promoted; rows that fail stay provisional. Other rows in the batch are not blocked from promotion. Whole-batch `validation_failed` response applies only to **single-match** failure (Q5b).

## Tests

| Test | Result |
|------|--------|
| `test_full_mvr_zero_matches_without_attrs_create_on_deliver` | Step-2 identity create → `validation_state: validated` |
| `test_multi_match_step2_promotes_provisional_bind` | Wrong Corp provisional → `validated` after multi-match deliver |
| `test_absurd_employer_fails_validation_stays_provisional` | Unchanged |
| `test_batch_step2_identity_only_found` | Unchanged (3 validated seed rows, preset `found`) |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 407 passed, 26 deselected
```

Manual repro:

```python
# bind_provisional("Andrea Kalmans", "Wrong Corp")
# step1: lookup name + email → step2 deliver
# Wrong Corp validation_state == "validated"
```

## For Grok + Paul

- **Q5a fixed** — validate on every query when provisional + MVR satisfied, including identity-only step-2.
- **Slice `1410` still queued** — multi-match step-2 truncation when research gate fires on partial batch.
- **Not committed** — awaiting review. Paul + Grok should test validation before `1410`.

Suggested commit message:

```
fix(query): run validate_entity on step-2 deliver for provisional rows

Route identity-only deliver through validation; validate each provisional
match in multi-match scopes (Q5a). Identity-only create-on-deliver promotes.
```

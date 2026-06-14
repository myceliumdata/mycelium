# Fix multi-match step-2 deliver truncation when research gate fires

## Summary

When the research gate blocks attribute research on a multi-match step-2 deliver, `results[]` now includes **all** scope identity rows instead of only `matched[0]`. Batch gating messages no longer mislabel validated rows as provisional.

## Root cause

`assemble_response_node` called `response_research_gated(query, matched[0])`, bypassing M8 batch deliver shape.

## Changes

| Area | Change |
|------|--------|
| `src/agents/responses.py` | `response_research_gated` accepts full `records` list; batch message summarizes N matches + M provisional rows |
| `src/agents/dispatch.py` | Pass `matched` (not `matched[0]`) to `response_research_gated` |
| `tests/test_mvr_batch_deliver.py` | `test_multi_match_research_gate_returns_all_identity_rows` |

## Test fixture note

Post-slice `1400`, Andrea @ Wrong Corp with valid employer promotes to `validated` on step 2 — research gate would not fire. The new test uses `bind_provisional("Andrea Kalmans", "A")` (validation failure, stays provisional) alongside seed Andrea @ Lontra (`validated`) to reproduce gated multi-match deliver.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 408 passed, 26 deselected
```

Manual:

1. Manufacture mixed batch (validated + provisional that fails validation)
2. Step 1 name-only Andrea + `email` → `total_matches: 2`
3. Step 2 deliver → `len(results) == 2`; message mentions "2 records" and provisional count

## For Grok + Paul

- Truncation fixed; M8 all-validated batch tests unchanged.
- **Not committed** — awaiting review.

Suggested commit message:

```
fix(query): return all matches when step-2 research gate blocks attrs

Multi-match deliver no longer truncates to matched[0]; fix gated
message for mixed validated/provisional batches.
```

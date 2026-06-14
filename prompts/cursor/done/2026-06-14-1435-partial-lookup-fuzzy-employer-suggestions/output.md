# Partial employer lookup: fuzzy suggestions before lookup_incomplete

## Summary

Partial employer-only lookups with 0 exact index hits now try `_rank_employer_suggestions` before returning `lookup_incomplete`. A typo like `{"employer":"654 Ventures"}` returns `lookup_suggested` with `645 Ventures` (`sequence_ratio`).

## Root cause

Slice `1430` added name fuzzy on partial 0-hit lookups; employer partial lookups still fell through to `lookup_incomplete` even when near-miss employer strings existed.

## Changes

| Area | Change |
|------|--------|
| `src/agents/entity_resolution.py` | New `_rank_employer_suggestions` — distinct registry employers, `normalize_field_index_value`, `SequenceMatcher`, same score/count thresholds as name fuzzy |
| `src/agents/target_resolve.py` | Partial 0-hit: name fuzzy first, then employer fuzzy; either → `lookup_suggested` |
| `tests/test_target_step1_lookup_clarity.py` | `test_partial_fuzzy_employer_lookup_suggested`, `test_partial_employer_shorthand_still_incomplete` |
| `docs/plans/fuzzy-lookup-policy.md` | Slice table status rows |
| `examples/networks/crm/README.md` | Step-1 employer typo + shorthand limitation |
| `src/network/introspection.py` | Policy note for partial employer fuzzy |

## Partial lookup fuzzy order

When both `name` and `employer` are present with 0 AND hits: **name fuzzy first**, then employer fuzzy. First non-empty suggestion list wins.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 411 passed, 26 deselected
```

## For Grok + Paul

- Employer fuzzy on partial 0-hit is done; name fuzzy (`1430`) unchanged.
- **Shorthand alias gap remains open:** `{"employer":"645"}` → `lookup_incomplete` (SequenceMatcher ~0.40). Track under alias/prefix design per `fuzzy-lookup-policy.md`.
- **Not committed** — awaiting review.

**Manual validation:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"654 Ventures"}'
# lookup_suggested → 645 Ventures
```

Suggested commit message:

```
fix(query): suggest fuzzy employer matches on partial lookup 0-hit

Extend bind-field fuzzy suggestions to employer (sequence_ratio);
shorthand aliases remain lookup_incomplete until alias design.
```

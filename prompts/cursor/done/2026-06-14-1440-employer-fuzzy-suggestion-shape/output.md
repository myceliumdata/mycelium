# Employer fuzzy: suggest corrected employer string (parity with name fuzzy)

## Summary

Employer fuzzy suggestions now represent the **corrected employer bind-field value** (`645 Ventures`), not an arbitrary person row (`Aaron Holiday`). Parity with name fuzzy: suggest, don't resolve — `requested_attributes` do not change step-1 outcome.

## Root cause

`_rank_employer_suggestions` set `entity_key=entity.name` (person) instead of the matched employer string.

## Changes

| Area | Change |
|------|--------|
| `src/agents/entity_resolution.py` | `_rank_employer_suggestions`: `entity_key` + `employer` = canonical employer string; `reason=employer_sequence_ratio`; omit `id`/`name` |
| `src/models/state.py` | `EntityKeySuggestion`: optional `id`/`name`; updated field descriptions |
| `src/agents/responses.py` | Employer-aware `_lookup_suggested_message` copy |
| `tests/test_target_step1_lookup_clarity.py` | Updated employer test + plural typo, attrs still suggested, retry-then-resolved |
| `docs/plans/fuzzy-lookup-policy.md` | Slice `1440`, retry contract, no auto-resolve |
| `examples/networks/crm/README.md` | `employer_sequence_ratio` + retry note |

## Employer retry contract

On employer `lookup_suggested`, retry with `lookup` using `suggestions[0].entity_key` (or `.employer`) as the corrected `employer` value. Same `requested_attributes` / step-2 flow as name fuzzy.

**Model choice:** `name` and `id` are `null` on employer-only suggestions; omitted from `public_dict` via `exclude_none=True`.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 414 passed, 26 deselected
```

## For Grok + Paul

- Employer fuzzy suggestion shape fixed; shorthand alias (`645`) still `lookup_incomplete`.
- **No auto-resolve** on fuzzy employer hit (batch expand deferred to caller retry).
- **Admin UI nit (out of scope):** `lookupFromSuggestion` maps `entity_key` → `name` bind field; employer suggestions should use `reason=employer_sequence_ratio` to set `employer` only — follow-up slice.
- **Not committed** — awaiting review.

**Manual validation:**

```bash
# Step 1 — suggest only
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Venture"}' \
  --attrs-json '["title","email"]'

# Step 2 — caller confirms
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Ventures"}' \
  --attrs-json '["title","email"]'
```

Suggested commit message:

```
fix(query): employer fuzzy suggests corrected employer string

Align employer typo suggestions with name fuzzy: suggest the bind-field
value for retry, do not pick a representative person or auto-resolve.
```

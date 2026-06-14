# Fix multi-match same-turn specialist scheduling after batch validate

## Summary

Multi-match step-2 deliver with requested attributes now runs attribute specialists in the **same turn** when `validate_entity` promotes the last provisional row and the research gate opens. Previously only single-match batches re-scheduled specialists after validation.

## Root cause

Supervisor defers specialist invoke when any scope row is provisional. `validate_entity_node` re-scheduled specialists only when `len(matched) == 1`, so multi-match batches promoted correctly but returned `assembled` with id-only `results[]` until a second query.

## Changes

| Area | Change |
|------|--------|
| `src/agents/dispatch.py` | Generalized post-validate specialist scheduling: drop `len(matched) == 1` guard; use `research_gate_allows` + attrs requested; `planner_context` with all entity ids for multi-match |
| `tests/test_mvr_create_on_deliver.py` | Extended `test_multi_match_step2_promotes_provisional_bind` — asserts `assembled`, `len(results) >= 2`, every row has mock `email`, research calls hit both entities |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 408 passed, 26 deselected
```

`test_multi_match_research_gate_returns_all_identity_rows` still passes (gate closed → no invoke).

## For Grok + Paul

- Closes **1400 nit N1** — multi-match promote + attrs in one deliver turn.
- **Not committed** — awaiting review.

**Manual validation (live CRM):**

1. Demote Andrea @ Wrong Corp to `provisional` in `entities.json`
2. Step 1: `lookup: {name: Andrea Kalmans}` + `email` → step 2 deliver **once**
3. Expect Wrong Corp `validated` **and** both rows have `email` in `results` (with API keys) without re-query

Suggested commit message:

```
fix(query): schedule specialists after multi-match batch validation

Re-invoke attribute specialists in the same turn when validate_entity
promotes the last provisional row and the research gate opens.
```

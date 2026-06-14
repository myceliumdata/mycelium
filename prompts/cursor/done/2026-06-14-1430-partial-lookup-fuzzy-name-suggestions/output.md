# Partial name lookup: fuzzy suggestions before lookup_incomplete

## Summary

Partial name-only lookups with 0 exact index hits now try `_rank_suggestions` before returning `lookup_incomplete`. A typo like `{"name":"Andrea Kalman"}` returns `lookup_suggested` with `Andrea Kalmans` (`sequence_ratio`) instead of asking for `employer`.

## Root cause

`resolve_target_step1` returned `lookup_incomplete` immediately for partial lookups after 0 AND hits. Fuzzy name ranking only ran on the full MVR path.

## Changes

| Area | Change |
|------|--------|
| `src/agents/target_resolve.py` | Partial 0-hit branch: if lookup includes non-empty `name`, call `_rank_suggestions`; non-empty → `lookup_suggested`, else unchanged `lookup_incomplete` |
| `tests/test_target_step1_lookup_clarity.py` | New `test_partial_fuzzy_name_lookup_suggested`; existing partial/full MVR tests unchanged |
| `examples/networks/crm/README.md` | Step-1 outcome note for partial name typo → `lookup_suggested` |
| `src/network/introspection.py` | One-line policy note on partial name 0-hit suggestions |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 409 passed, 26 deselected
```

## For Grok + Paul

- Fixes Claude/MCP repro: `{"name":"Andrea Kalman"}` → `lookup_suggested`.
- **Program 2 gate table** (`docs/manual-checks/2026-06-13-program2-post-program-gate.md`): add row — partial name typo 0-hit → `lookup_suggested` (not only `lookup_incomplete`).
- Employer-only partial fuzzy **out of scope** this slice.
- **Not committed** — awaiting review.

**Manual validation:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalman"}'
# lookup_suggested, suggestions include Andrea Kalmans
```

Suggested commit message:

```
fix(query): suggest fuzzy name matches on partial lookup 0-hit

When partial lookup has no exact index hits but name is near-miss,
return lookup_suggested instead of lookup_incomplete.
```

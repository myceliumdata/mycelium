# Rename suggestions[].entity_key → suggested_lookup (target protocol vocabulary)

## Summary

Public `suggestions[]` now use **`suggested_lookup`** (target-protocol bind map) instead of retired `entity_key`. `EntityKeySuggestion` renamed to **`LookupSuggestion`** with central `lookup_suggestion()` builder.

## Root cause

MVR redesign M9 removed query `entity_key`, but suggestion responses still exposed `suggestions[].entity_key` — confusing for employer typos (`645 Ventures` looked like a query field).

## Changes

| Area | Change |
|------|--------|
| `src/models/state.py` | `LookupSuggestion` + `lookup_suggestion()` helper; optional `id`/`name` |
| `src/agents/entity_resolution.py` | All rankers use `lookup_suggestion()` |
| `src/agents/target_resolve.py` | `same_name_different_employer` sets full `suggested_lookup` |
| `src/agents/responses.py` | Messages reference `suggested_lookup` |
| `src/graphs/core.py` | Checkpoint allowlist → `LookupSuggestion` |
| `src/network/introspection.py` | Policy + status display |
| `admin-ui/` | `LookupSuggestion` type; `lookupFromSuggestion` merges `suggested_lookup` (fixes employer click) |
| Tests | Public JSON shape smokes; legacy path updated |
| Docs | `fuzzy-lookup-policy.md`, `architecture.md`, CRM README, phase1 superseded note |

## Retry contract

On `lookup_suggested`, retry step 1 with `lookup` merged from `suggestions[].suggested_lookup` (or `suggestions[].id` for one known row). **Do not** send `entity_key`.

| `reason` | `suggested_lookup` |
|----------|-------------------|
| `sequence_ratio` | `{"name": "Andrea Kalmans"}` |
| `employer_sequence_ratio` | `{"employer": "645 Ventures"}` |
| `same_name_different_employer` | `{"name": "…", "employer": "…"}` |

Employer-only fuzzy: `id`/`name` omitted from `public_dict` (1440 nit closed).

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 419 passed, 26 deselected
```

## For Grok + Paul

- Suggestion vocabulary aligned with target protocol; **breaking change** (no `entity_key` alias).
- Admin employer suggestion click now sets `employer` field correctly.
- **MCP restart** recommended for agent consumers after merge.
- **Not committed** — awaiting review.

**Manual validation:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Venture"}' --json
# suggestions[0].suggested_lookup.employer == "645 Ventures"
# suggestions[0].entity_key absent
```

Suggested commit message:

```
refactor(query): replace suggestions[].entity_key with suggested_lookup

Rename EntityKeySuggestion to LookupSuggestion; suggestion retry hints
use target-protocol lookup maps instead of retired entity_key vocabulary.
```

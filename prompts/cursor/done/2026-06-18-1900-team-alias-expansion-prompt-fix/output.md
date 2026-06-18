# Output — team alias expansion prompt fix

## Summary

Lazy team nickname expansion now asks the LLM for **canonical bind strings** only (no entity ids in prompt or structured output). The framework maps returned values to registry rows via `lookup_by_bind_values`; unknown strings are dropped. Mashups like `Washington Red Sox` return empty → `not_found` with no alias pollution.

## Changes

| Area | Change |
|------|--------|
| `bind_alias_expansion.py` | Prompt rewrite; `_FieldAliasProposal.canonical_values`; `_canonical_values_to_entity_ids()`; `AliasExpander` returns canonical strings |
| `guide.md` | Full Lahman labels, mashup → `not_found`, nicknames via lazy expansion |
| `test_closed_identity_lazy_aliases.py` | Mock returns canonical names; mashup, Boston exact, Miracle Mets tests |
| `test_strict_record_type_routing.py` | Mock contract updated |

## Mapping helper

`_canonical_values_to_entity_ids(registry, field_key, canonical_values)` — strip each value, `lookup_by_bind_values`, dedupe ids; skip unknowns.

## Mock contract

```python
# Returns canonical team strings, not entity ids
if query_value == "Bronx Bombers":
    return ["New York Yankees"]
if query_value == "Dodgers":
    return ["Brooklyn Dodgers", "Los Angeles Dodgers"]
```

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **509** smoke passed |

## For Grok + Paul

- **Hand-retest** on refreshed baseball root: `{"lookup": {"team": "Washington Red Sox"}}` → `not_found`, no new `field_aliases` on Cleveland/Nationals rows.
- Confirm `Boston Red Sox`, `Dodgers`, `Bronx Bombers` still behave as expected with live LLM (Q15).
- Player-grain prompt uses same generic `{field}` builder — no separate redesign this slice.
- Update HOLD.md queue.
- No commit (per workflow).

**Suggested commit message:**

```
fix(aliases): LLM returns canonical bind values, not entity ids

Rewrite team nickname expansion prompt to reject mashups; map canonical
strings to registry ids in framework. Prevents Washington Red Sox-style
alias pollution on bootstrap_only teams.
```

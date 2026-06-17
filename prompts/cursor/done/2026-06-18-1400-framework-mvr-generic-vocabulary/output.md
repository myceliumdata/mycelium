# Output — framework MVR generic vocabulary

## Summary

Removed CRM-shaped field hardcoding from framework `src/`: identity models, context assembly, validation, suggestions, registry helpers, bootstrap, and specialists now follow active MVR `bind_fields`. CRM example network behavior unchanged (still `name` + `employer` in seed and capstones).

## Files changed (high level)

| Area | Change |
|------|--------|
| `models/state.py` | `IdentityRecord.bind_values`; `LookupSuggestion` drops `name`/`employer`; reason strings updated |
| `entity_registry.py` | `registry_entity_to_match(mvr=…)`; removed `lookup_by_bind_key`, `ensure_bound_entity`, `bind_provisional` |
| `attribute_write.py` | `bind_provisional()` helper (CRM-shaped thin wrapper) |
| `context.py`, `snapshots.py` | Dynamic MVR bind fields via `mvr_bind_field_set()` |
| `entity_validation.py` | `run_mvr_validation(entity, mvr=…)` driven by MVR + `attribute_map` |
| `entity_resolution.py`, `target_resolve.py` | Generalized fuzzy + conflict suggestions |
| `responses.py`, `dispatch.py` | Identity summary keys from MVR; updated suggestion messages |
| `category_mvr_bootstrap.py` | `EXAMPLE_BIND_FIELD_CATEGORY_FALLBACK` |
| `default_seed.py` | Generic seed row → `ensure_entity_bind_fields` per grain MVR |
| `network/mvr.py` | `mvr_bind_field_set()`; neutral default description |
| Specialists + template | `IdentityRecord(bind_values=…)` |
| `mycelium_mcp/server.py`, `network/create.py` | Neutral copy |
| `docs/architecture.md` | Identity/results bullets MVR-generic |
| `tests/test_mvr_generic_vocabulary.py` | Guard + `bind_from_record` test |

## Breaking changes (for colleagues)

| Surface | Before | After |
|---------|--------|-------|
| `IdentityRecord` | `id`, `name`, `employer` | `id`, `bind_values` dict |
| `LookupSuggestion` | + optional `name`, `employer` | `suggested_lookup` only (+ optional `id`) |
| Suggestion `reason` | `same_name_different_employer`, `employer_sequence_ratio` | `same_bind_field_conflict`, `bind_field_fuzzy_match` |
| `EntityRegistry` | `lookup_by_bind_key`, `ensure_bound_entity`, `bind_provisional` | Use `lookup_by_bind_values`, `ensure_entity_bind_fields`, `attribute_write.bind_provisional` |
| MCP `IdentityRecord` schema | id + name + employer | id + bind_values |

**Admin UI / MCP clients:** suggestion retry should merge `suggested_lookup` only (admin-ui already does). External tools asserting `suggestion.name` or old reason strings need updates.

## Exit criteria

| # | Status |
|---|--------|
| E1 | No `frozenset({"name", "employer"})` in `src/` |
| E2 | `IdentityRecord` uses `bind_values`; MCP schema updated |
| E3 | `run_mvr_validation` driven by MVR + categories map |
| E4 | CRM capstones + `./bin/ci-local` green — **474** smoke tests |
| E5 | Breaking changes listed above |
| E6 | `rg 'CRM-shaped|CRM people' src/` → no matches |

## For Grok + Paul

- Colleagues reviewing framework: point them to `IdentityRecord` / `LookupSuggestion` / removed registry helpers.
- Admin-ui `LookupSuggestion` type still has optional legacy fields in TS — optional follow-up to align types with MCP schema.
- CRM `examples/networks/crm-metering` query JSON unchanged (valid CRM MVR).

**Suggested commit message:**

```
refactor(mvr): generic bind vocabulary; remove CRM field hardcoding

IdentityRecord and suggestions use bind_values; validation and context
follow active MVR; drop name/employer-only registry helpers.
```

# Output — bootstrap perf profile-driven fix

## Summary

Profile showed ~97% of Lahman handler cProfile time in `build_field_indexes` via `_rebuild_field_indexes` on every deferred `save_entity` — including ~33k alias-only `add_bind_alias` rows where `entity.bind_values` never change. `add_bind_alias` now updates `bind_index` only and calls `_save(rebuild_field_indexes=False)`. `lookup_by_bind_values` still resolves aliases via `bind_index` (not field indexes). `commit_deferred_save` still runs one full rebuild at grain flush.

## Files changed

| File | Change |
|------|--------|
| `src/agents/entity_registry.py` | `_save(rebuild_field_indexes=...)`; `add_bind_alias` skips rebuild |
| `tests/test_entity_store_evolution.py` | Alias skip rebuild spy; new-entity save still rebuilds + lookup |

## Exit criteria

| # | Status |
|---|--------|
| E1 | Profile results in prompt; implementation matches O1 verdict |
| E2 | Alias path avoids full field-index rebuild (test proves) |
| E3 | Lahman multi-team test green (existing) |
| E4 | `./bin/ci-local` green — **472** smoke tests passed |
| E5 | Paul timing re-run pending |

## Why `lookup_by_bind_values` still works

Alias attach only adds a key to `_data.bind_index`. `lookup_by_bind_values` reads `bind_index` directly (`make_bind_key` → entity id). Field indexes (`lookup_by_field`, `lookup_by_target_lookup`) are unchanged because `entity.bind_values` are unchanged.

## For Grok + Paul

- **Re-run timing** after approval — compare to Test 6 (**1,202 s** real). Expect meaningful drop from skipping ~33k full index scans on fresh bootstrap (alias rows) plus avoiding redundant rebuilds on warm duplicate `ensure_entity_bind_fields` path where applicable.
- Record in `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` (add Test 7 row or update comparison table).
- **Not in scope:** incremental index update for new-player `save_entity` (profile showed specialist path already cheap at ~91 s cumtime).

**Suggested commit message:**

```
perf(bootstrap): skip field-index rebuild on alias-only bind attach

Avoid full _rebuild_field_indexes on add_bind_alias when bind_values
unchanged; profile-driven Lahman bootstrap fix.
```

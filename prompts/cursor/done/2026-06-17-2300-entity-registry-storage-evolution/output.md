# Entity registry storage — deferred bootstrap save + minisql_v1

## Summary

Extracted **`EntityStore`** (`src/storage/entity_store.py`) for per-grain persistence. `EntityRegistry` delegates load/save; public API unchanged. Network bootstrap wraps handlers in **`bootstrap_deferred_save()`** — one flush per grain at end. Entity **`minisql_v1`** migration at threshold via shared `src/storage/minisql_v1.py` entity adapters.

## Key changes

| Area | Change |
|------|--------|
| `src/storage/entity_store.py` | `entities_document_v1` JSON + `minisql_v1` SQLite; strategy at `entities/<grain>.storage_strategy.json` |
| `src/storage/minisql_v1.py` | `load_entities_document`, `save_entities_document`, `migrate_entities_document_v1_json` |
| `src/agents/entity_registry.py` | `EntityStore` delegation; `bootstrap_deferred_save()`; `deferred_save()` / `commit_deferred_save()`; optimize hooks |
| `src/network/bootstrap/run.py` | `with bootstrap_deferred_save(): handler.run(ctx)` |
| `tests/test_entity_store_evolution.py` | Deferred flush, minisql migration, backup, lookup roundtrip |
| `docs/architecture.md` | EntityStore, deferred bootstrap, minisql paths; identity-agent refactor deferred |

**Bootstrap deferral:** Module-level `bootstrap_deferred_save()` increments depth; all grains in `_registry` get `commit_deferred_save()` on exit. Lahman `team` + `player` registries both flush once when handler completes.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 462 passed, 96 deselected
```

## For Grok + Paul

- **Timing test 5** (manual): Paul + Grok run per `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`:

```bash
export BENCHMARK_ROOT=/tmp/mycelium-baseball-benchmark
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root "$BENCHMARK_ROOT" --yes --no-default
```

Compare **real** time to baseline (~12,600 s / ~3.5 h) and test 3 when recorded. This slice is the primary baseball bootstrap perf change.

- Storage evolution program completes after slice 5 gate (timing test 5 + Paul decision).
- Post-baseball **identity-agent** refactor remains deferred (Option C; architecture note).
- Suggested commit:

```
feat(entities): deferred bootstrap save and minisql_v1 entity store migration
```

- Do not commit from Cursor unless Paul asks.

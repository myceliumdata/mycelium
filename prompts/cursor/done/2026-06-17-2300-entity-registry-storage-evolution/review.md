# Review: Entity registry storage — deferred bootstrap save + `minisql_v1`

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-17

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` (Grok re-run) | **462 passed**, 96 deselected; ruff clean; admin-ui build ok |

Matches Cursor `output.md` claim (+5 tests vs slice 2).

---

## Delivery

| Artifact | Status |
|----------|--------|
| `src/storage/entity_store.py` | ✅ `entities_document_v1` + `minisql_v1`, strategy, backup rename |
| `src/storage/minisql_v1.py` | ✅ Entity document tables + load/save/migrate |
| `src/agents/entity_registry.py` | ✅ Delegation, deferred save, optimize hooks, `bootstrap_deferred_save()` |
| `src/network/bootstrap/run.py` | ✅ `with bootstrap_deferred_save(): handler.run(ctx)` |
| `tests/test_entity_store_evolution.py` | ✅ 5 smoke tests |
| `docs/architecture.md` | ✅ EntityStore, deferred bootstrap, identity-agent deferred |
| Prompt removed from `next/` | ✅ |

---

## Spec compliance (Option C)

| # | Criterion | Status |
|---|-----------|--------|
| E1 | `EntityStore` only — `EntityRegistry` API unchanged | ✅ |
| E3 | `src/storage/entity_store.py` | ✅ |
| E5 | `entities/<grain>.storage_strategy.json`, strategy `entities_document_v1` | ✅ |
| E6–E8 | minisql reuse, threshold env, JSON backup rename | ✅ |
| E9 | Bootstrap one flush per grain | ✅ `bootstrap_deferred_save` + test |
| E10 | `get_entity_registry()` / lookup/bind unchanged | ✅ |
| E11 | CRM + capstones + Lahman tests | ✅ (in smoke run) |

---

## Diff reviewed

- `src/storage/entity_store.py` (full)
- `src/storage/minisql_v1.py` (entity section)
- `src/agents/entity_registry.py` (store delegation, deferral, optimize)
- `src/network/bootstrap/run.py`
- `tests/test_entity_store_evolution.py` (full)
- `docs/architecture.md` (entities bullet)

---

## Design critique

**Strong:**

- **Deferred bootstrap is the main perf fix:** `_defer_flush()` skips disk during handler loop; `bootstrap_deferred_save()` commits every grain in `_registry` once on exit — addresses ~58k `player.json` rewrites.
- Clean Option C split: `EntityStore` persistence, `EntityRegistry` domain logic and public API.
- Baseball first commit at ≥50 entities can migrate to `minisql_v1` **without ever writing a full JSON file** (migrate tolerates missing JSON; `save` fills SQLite) — excellent emergent behavior for Lahman.
- `MYCELIUM_ENTITY_OPTIMIZE_STORAGE_THRESHOLD` with fallback to shared knob — per E7.
- Tests prove single flush under deferral, per-save flush without, migration + backup + lookup roundtrip.

**Honest limits (non-blocking):**

1. **`save_entities_document` is full replace** per flush (like specialist v1) — acceptable post-bootstrap; query-path incremental saves are smaller than 58k-row JSON rewrites.
2. **`bootstrap_deferred_save` commits all instantiated grains** in `_registry` — correct for Lahman (team + player); grains never touched during bootstrap are not flushed (expected).
3. **Architecture line on specialist `minisql_v1`** still says entity reuse is “follow-up slice” — entities bullet is updated; one sentence stale (nit).

---

## Nits

| # | Item |
|---|------|
| N1 | `docs/architecture.md` ~L191: update “follow-up slice” → entity stores now use same module |

---

## For Paul

**Commit message:**

```
feat(entities): deferred bootstrap save and minisql_v1 entity store migration
```

**Timing test 5** — primary validation of this slice:

```bash
export BENCHMARK_ROOT=/tmp/mycelium-baseball-benchmark
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root "$BENCHMARK_ROOT" --yes --no-default
```

Compare **real** to baseline **12,600 s (~3.5 h)** and test 3 estimate **8,100 s (~2 h 15 m)**. Expect large improvement from single flush + optional entity SQLite.

**Program:** Storage evolution slices 1–4 complete; slice 5 = test 5 + your call on push/demo.

**Push:** Local only until you ask.
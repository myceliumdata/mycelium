# Bootstrap perf — profile-driven dopey-inefficiency fix

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** First Cursor slice tomorrow — after Grok fills § Profile results below from overnight `cProfile` run.

**Principles (Paul, June 2026):**

- **Profile first** — this slice implements only what profiling proved; no speculative batch loaders.
- **Clarity over cleverness** — smallest obvious fix; readable code paths; no bootstrap-only SQL identity pipeline.
- **Eliminate dopey inefficiencies** — work that buys nothing (e.g. full index rebuild when only `bind_index` changed).

**Parent:** [`docs/manual-checks/profile-lahman-bootstrap-overnight.md`](../../../docs/manual-checks/profile-lahman-bootstrap-overnight.md), [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../../../docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md) Test 6.

---

## Profile results (Grok fills before Cursor starts)

| Metric | Value |
|--------|-------|
| Test 6 `time -p` real (s) | **1,202.19** (user 1142.45, sys 42.09) — 23,777 entities, 57,627 binds |
| Profile run date | 2026-06-17 overnight (`bin/overnight-lahman-profile`) |
| Profile mode | **Warm re-bootstrap** on post–test 6 root (`entities_committed=29`; most binds already on disk) |
| Handler wall (cProfile) | 4725 s (~79 min — cProfile overhead ~10×; ~8 min wall estimated) |
| `_rebuild_field_indexes` calls | **23,844** |
| `build_field_indexes` cumtime | **4590 s** (~**97%** of handler time) |
| `add_bind_alias` calls | **0** (warm run skips alias rows already in `bind_index`; fresh test 6 ≈ **33,616** alias rows) |
| Specialist `write_bind_fields_multi` cumtime | **91 s** (incremental upserts **not** the bottleneck) |

**Grok verdict:** **Implement O1.** Profile proves deferred-bootstrap `_save()` spends almost all time in full `build_field_indexes()` scans (~24k rebuilds on warm run; ~58k on fresh). Code path: `add_bind_alias` → `save_entity` → `_save` → `_rebuild_field_indexes` even when only `bind_index` changes. **Do not** add batch loader or incremental field-index rebuild in this slice (clarity). **Do not** touch specialist/minisql path (already cheap).

**Top cumulative (handler):**

```
ensure_entity_bind_fields  4717s  (warm: duplicate seed rows still call write_bind_fields)
write_bind_fields          4716s
_rebuild_field_indexes     4623s  (23,844 calls)
build_field_indexes        4590s  (tottime 647s — dominates)
write_bind_fields_multi      91s  (specialist — fine)
upsert_entity_record         41s
```

**Code confirmation** (`entity_registry.py`): during `bootstrap_deferred_save`, `_save()` rebuilds indexes without persisting; `add_bind_alias` calls `save_entity(entity)` unchanged → wasted full scan.

**Raw log:** `/tmp/lahman-bootstrap-test6.txt` · **prof:** `/tmp/lahman-bootstrap-test6.prof` (Paul's machine, not committed)

---

## Locked scope from profile (update after § Profile results)

**Default if profile confirms alias/index hypothesis:**

| # | Decision |
|---|----------|
| O1 | **`add_bind_alias` must not call full `_rebuild_field_indexes()`** when `entity.bind_values` unchanged — update `bind_index` only during deferred bootstrap (and query path if same pattern). |
| O2 | **`lookup_by_bind_values` stays on `bind_index`** — do not break alias resolution. |
| O3 | **Field indexes** must still be correct when `bind_values` / `save_entity` actually changes bind fields. |
| O4 | **No batch Lahman loader** — no SQL bulk identity import; no skipping `ensure_entity_bind_fields` for new players. |
| O5 | **CRM + Lahman tests green**; add one test proving alias attach does not rebuild field indexes (spy or call-count). |

Profile **confirms** rebuild dominates; alias fast-path is the smallest high-impact fix for fresh bootstrap (~59% of rebuild calls). Optional incremental index update for **new** players is **out of scope** unless Paul asks after re-measure.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/agents/entity_registry.py` — `add_bind_alias`, `_save`, `_rebuild_field_indexes`, `assign_bind_index`
- `src/agents/field_index.py` — `build_field_indexes`
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`
- `tests/test_lahman_seed_handler.py`, `tests/test_multi_mvr_entity_stores.py`
- `tests/test_entity_store_evolution.py` (deferred save)

---

## Implement (after profile confirms)

### Likely change (alias fast path)

- `add_bind_alias`: assign `bind_index` key; **do not** call `save_entity` if that triggers full field-index rebuild with unchanged `bind_values`.
- Prefer explicit method e.g. `attach_bind_alias(entity_id, bind_values)` that updates `_data.bind_index` only and skips `_rebuild_field_indexes` when field-index inputs unchanged.
- Document in `output.md` why query-time `lookup_by_bind_values` still works.

### If profile shows new-player `save_entity` rebuild is also hot

- **Optional second change** only if § Profile results shows material `build_field_indexes` cost on **new** player path: incremental index update for changed bind fields only — still **no** batch loader. If marginal vs alias, **skip** (clarity).

---

## Tests

| Test | Assert |
|------|--------|
| Multi-team alias (existing Lahman fixture) | Still 1 player, 2 bind keys, same id |
| Alias attach index behavior | Field-index rebuild **not** invoked on alias-only attach (mock/spy) |
| New player bind | Field indexes / lookup still work after `ensure_entity_bind_fields` |
| CRM bootstrap | Unchanged entity counts |

---

## Scope boundaries (strict)

**May modify:**

- `src/agents/entity_registry.py`
- `tests/test_lahman_seed_handler.py` and/or `tests/test_entity_registry_*.py` (new tests)
- `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` — Test 7 row template **only if** Grok asks post-slice

**Do not modify:**

- `lahman_seed.py` batch SQL paths
- `src/storage/minisql_v1.py` (incremental upsert already shipped)
- `TODO.md`
- Specialist write path beyond registry side effects

---

## Explicit non-goals

- Batch/bootstrap SQL identity import
- Parallel workers / multiprocessing
- Removing deferred entity flush
- Entity `save_entities_document` incremental bulk
- Sub-minute guarantee — aim for obvious win, re-measure with Paul

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | § Profile results filled; implementation matches Grok verdict |
| E2 | Alias path avoids full field-index rebuild when profile targeted it |
| E3 | Lahman multi-team test green |
| E4 | `./bin/ci-local` green |
| E5 | Paul re-runs timing; Grok records Test 7 or updates Test 6 comparison in `output.md` notes |

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **For Grok + Paul** in `output.md`: measured before/after if Paul provides second `time -p`.

## When finished

Per `prompts/cursor/WORKFLOW.md` — no commit/push.

**Suggested commit message:**

```
perf(bootstrap): skip field-index rebuild on alias-only bind attach

Avoid full _rebuild_field_indexes on add_bind_alias when bind_values
unchanged; profile-driven Lahman bootstrap fix.
```
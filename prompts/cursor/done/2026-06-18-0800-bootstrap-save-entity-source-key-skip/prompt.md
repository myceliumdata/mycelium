# Bootstrap perf — skip source-key rebuild on bind-only `save_entity`

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** Run **before** `2026-06-18-0900-registry-source-keys-polish-nits.md` (this filename sorts first).

**Principles (Paul, June 2026):**

- **Profile / timing gates first** — implement only the proven remaining gap; no batch loaders or bootstrap SQL shortcuts.
- **Clarity over cleverness** — mirror the test 7 `add_bind_alias` and `c96c5e2` `set_source_keys` patterns.
- **Eliminate dopey inefficiencies** — full index rebuild when inputs did not change.

**Parent:** [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../../../docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md) tests 7, 8, 8b. Follow-up to commit `c96c5e2`.

---

## Timing context (Grok — do not re-profile; implement from gates)

| Run | real (s) | Notes |
|-----|----------|-------|
| **Test 7** | **555.38** (~9 min) | Pre–`source_keys` (`f45b65c`). ~24k new-player `save_entity` field-index rebuilds only. |
| **Test 8** | **2,946.32** (~49 min) | Regression: per-row full `_rebuild_source_key_index()` on `set_source_keys` + `add_bind_alias`. |
| **Test 8b** | **1,398.87** (~23 min) | Post `c96c5e2`: incremental `set_source_keys` + alias skip. **2.1×** vs test 8; still **2.52×** vs test 7. |

**Grok verdict:** **Implement O1.** Remaining gap is ~24k `save_entity` calls during Lahman bootstrap (`ensure_entity_bind_fields` → `write_bind_fields` → `save_entity`) each running full `_rebuild_source_key_index()` even though `source_keys` are written **after** via `set_source_keys`. Test 7 had no `source_key_index` at all. Skipping source-key rebuild on bind-only `save_entity` should recover test 7 ballpark (~9 min). **Do not** add incremental field-index rebuild in this slice.

**Lahman handler order (unchanged):**

```
ensure_entity_bind_fields → save_entity (bind only, source_keys {})
set_source_keys           → incremental source_key_index (c96c5e2)
```

**Code confirmation** (`entity_registry.py`):

- `save_entity` → `_save()` defaults `rebuild_source_key_index=True` → full entity scan per new player.
- `set_source_keys` / `add_bind_alias` already pass `rebuild_source_key_index=False` (`c96c5e2`).
- `commit_deferred_save` still runs one full `_rebuild_source_key_index()` at grain flush — correctness backstop.

---

## Locked scope

| # | Decision |
|---|----------|
| O1 | **`save_entity` must not call full `_rebuild_source_key_index()`** when only bind/entity fields change — source keys are updated only via `set_source_keys` (incremental index). |
| O2 | **`save_entity` still rebuilds field indexes** when `rebuild_field_indexes=True` (default) — unchanged test 7 behavior for new players. |
| O3 | **`lookup_by_source_key` stays correct** during deferred bootstrap: `set_source_keys` runs incremental index update after bind save; `commit_deferred_save` full rebuild at flush. |
| O4 | **Non-deferred `save_entity`** (query-time `write_bind_fields`) must not persist a stale `source_key_index` on disk. Bind-only writes do not change `entity.source_keys`; index entries already correct. Document in `output.md`. |
| O5 | **No Lahman handler changes** — registry-only fix. |
| O6 | **Optional (same slice if trivial):** `add_field_alias` → `_save(rebuild_field_indexes=True, rebuild_source_key_index=False)` — field aliases do not touch source keys (one-line parity with `add_bind_alias`). |

**Out of scope:** incremental field-index update for new players; batch `set_source_keys`; `lahman_seed.py` SQL paths; specialist/minisql.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/agents/entity_registry.py` — `save_entity`, `_save`, `set_source_keys`, `commit_deferred_save`
- `src/agents/attribute_write.py` — `write_bind_fields` → `save_entity` (only registry caller)
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py` — create + `set_source_keys` order
- `tests/test_entity_store_evolution.py` — `test_add_bind_alias_skips_field_index_rebuild`, `test_set_source_keys_skips_full_index_rebuilds`
- `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` — test 8b remaining-gap note

---

## Implement

### Primary change (`save_entity`)

- After storing entity in `_data.entities`, call `_save(rebuild_source_key_index=False)` (keep default `rebuild_field_indexes=True`).
- Add a one-line docstring note: source keys and `source_key_index` are maintained by `set_source_keys`; bind-only saves skip full source-key scan.

**Do not** add a public `rebuild_source_key_index` kwarg on `save_entity` unless tests require it — prefer fixed behavior matching O1.

### Optional parity (`add_field_alias`)

- If touching `add_field_alias`, skip source-key rebuild only; field-index rebuild still required for new alias values.

### Docs (timing gate template)

- In `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`, add **Test 8c** row under test 8 section with `*pending Paul re-run*` and note expected ~test 7 ballpark. **Do not** fill Paul's numbers — Grok records after manual gate.

---

## Tests

| Test | Assert |
|------|--------|
| Bind-only `save_entity` | `_rebuild_source_key_index` **not** invoked (mock/spy), mirroring `test_set_source_keys_skips_full_index_rebuilds` |
| Field indexes still work | Existing `test_save_entity_rebuilds_field_indexes_for_lookup` still passes (`_rebuild_field_indexes` still called) |
| Source key round-trip | Existing `test_lookup_by_source_key_round_trip` still passes (`set_source_keys` + reload) |
| Lahman multi-team | `tests/test_lahman_seed_handler.py` unchanged behavior |
| CRM bootstrap | Smoke / entity store tests green |

Add `test_save_entity_skips_source_key_index_rebuild` (or equivalent name) in `tests/test_entity_store_evolution.py`.

---

## Scope boundaries (strict)

**May modify:**

- `src/agents/entity_registry.py`
- `tests/test_entity_store_evolution.py` (and/or existing registry tests)
- `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` — Test 8c template row only

**Do not modify:**

- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`
- `src/storage/*`, specialist paths
- `TODO.md`
- `prompts/cursor/next/2026-06-18-0900-registry-source-keys-polish-nits.md` (Grok updates P4 after review)

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | `save_entity` skips full source-key rebuild; field-index rebuild on bind save unchanged |
| E2 | New unit test with spy/mock proves skip behavior |
| E3 | `./bin/ci-local` green |
| E4 | Test 8c row stubbed in timing-gates doc |
| E5 | `output.md` notes Paul should re-run Test 8c command (below) |

**Paul manual gate (post-review):**

```bash
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root /tmp/mycelium-baseball-benchmark --yes --no-default
```

Expect **~555 s real** (± reasonable variance). Record as **Test 8c** in timing-gates doc.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **For Grok + Paul** in `output.md`: note polish slice **P4** (batch `set_source_keys`) is **obsolete** after this slice + `c96c5e2`; drop or mark done when updating polish prompt.

## When finished

Per `prompts/cursor/WORKFLOW.md` — no commit/push.

**Suggested commit message:**

```
perf(bootstrap): skip source-key rebuild on bind-only save_entity

Lahman bootstrap calls save_entity before set_source_keys; each call
was scanning all entities for source_key_index. Mirrors c96c5e2 fast
path; expect test 7 ballpark (~9 min) on Test 8c.
```
# Entity registry storage — batch save + `minisql_v1` evolution

> **HOLD** — **Do not claim** until Paul + Grok complete **timing test 3** (post slice 2) and move this file to `prompts/cursor/next/`.

**Program:** Storage evolution (specialist → entity). **Slice 4 of 5.**

| Prerequisite | Status |
|--------------|--------|
| Slice 1 approved | `2026-06-17-1900-specialist-optimize-storage-check` |
| Slice 2 approved | `2026-06-17-2100-specialist-minisql-v1-migrate` |
| Timing test 3 recorded | Paul + Grok manual gate — **required before claim** |

**Context:** Baseball bootstrap slowness is dominated by **entity registry** I/O (`entities/team.json`, `entities/player.json`), not specialist category storage. `EntityRegistry._save()` rewrites the full JSON document on **every** `save_entity` — including each `ensure_entity_bind_fields` / `add_bind_alias` call in `LahmanSeedHandler` (~tens of thousands of flushes per refresh). Specialist storage evolution (slices 1–2) does not fix this. Paul wants the **same threshold / migrate pattern** applied to entity storage, plus bootstrap-friendly batch persistence.

**After this slice:** Paul + Grok run **timing test 5** (manual).

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| E1 | **Entity storage is framework-owned** (not a taxonomy specialist module). Introduce a dedicated store abstraction parallel to `SpecialistStorage` — e.g. `EntityStore` in `src/agents/entity_store.py` or `src/storage/entity_store.py`. |
| E2 | **Per-grain stores** unchanged at the path level (`entities/<grain>.json` per `network.json` grains). |
| E3 | **Reuse `minisql_v1`** from slice 2 shared module — do not fork SQLite logic. |
| E4 | **Threshold policy** mirrors specialist slice 1: env `MYCELIUM_ENTITY_OPTIMIZE_STORAGE_THRESHOLD` (default **50**) or shared `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD` if you document one knob for both; per-grain evaluation independent. |
| E5 | **Bootstrap batching:** `run_network_bootstrap` (and handlers like `LahmanSeedHandler`) must **defer disk flush** until bootstrap completes — one `_save()` per grain at end, not per row. Query-path incremental saves unchanged. |
| E6 | **Protocol/API unchanged:** `get_entity_registry()`, lookup/bind APIs, multi-grain manifest behavior unchanged from caller view. |
| E7 | **CRM regression:** 15-entity CRM refresh, capstones, Program 2 matrix green. |
| E8 | **Baseball smoke:** `tests/test_lahman_seed_handler.py` + refresh smoke stay green; add test proving bootstrap does not call `_save` per entity (mock/spy). |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/plans/storage-evolution-program.md`
- `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` (release gate)
- `prompts/cursor/done/2026-06-17-2100-specialist-minisql-v1-migrate/` (shared `minisql_v1` module)
- `src/agents/entity_registry.py` — `_save`, `save_entity`, `add_bind_alias`
- `src/network/bootstrap/run.py` — `run_network_bootstrap`
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`
- `prompts/cursor/done/2026-06-17-1400-multi-mvr-entity-stores/prompt.md`
- `docs/plans/baseball-example-program.md` — scale notes

---

## Architecture target

```
EntityRegistry (per grain)
    → EntityStore (persistence backend)
        → versioned JSON (entities_document_v1) OR minisql_v1
    → optimize_storage() before _save when entity_count >= threshold
        → migrate_to("minisql_v1") via shared storage/minisql_v1.py

Bootstrap:
    run_network_bootstrap
        → registry.begin_deferred_save()  [or context manager]
        → handler commits rows in memory
        → registry.commit_deferred_save()  # one flush per grain
```

**Strategy metadata:** per-grain `entities/<grain>.storage_strategy.json` (or co-located strategy file — pick one layout, document).

---

## Implement

### 1 — `EntityStore` abstraction

Extract load/save/migrate from `EntityRegistry` into a store class:

- `load() -> EntitiesDocument` (or dict)
- `save(document) -> None`
- `current_strategy() -> str`
- `migrate_to(target: str) -> None`
- `entity_count()` for threshold

`EntityRegistry` keeps indexes, lookup, bind logic; delegates persistence.

### 2 — Deferred save for bootstrap

- Add `deferred_save: bool` flag or context manager on `EntityRegistry`
- While deferred: mutate memory only; skip `_save()`
- `commit()` flushes once
- Wire `run_network_bootstrap` to wrap handler execution with deferred save **per grain registry** used

Ensure query-time `save_entity` still saves immediately when not in bootstrap/deferred mode.

### 3 — `optimize_storage` + `migrate_to` for entity store

Mirror specialist pattern:

```python
def optimize_storage(self) -> bool:
    if self._store.current_strategy() != "entities_document_v1":  # name the JSON strategy explicitly
        return False
    return self.entity_count() >= self.optimize_storage_threshold()
```

Call before `_save()` on non-deferred paths when threshold crossed.

Implement `migrate_to("minisql_v1")` using shared module — map `entities` + `bind_index` into SQLite; backup JSON; update strategy file.

### 4 — Multi-grain

Each grain (`person`, `team`, `player`) has its own store file and independent threshold/migration. Baseball `player` grain may migrate; CRM `person` grain may stay JSON (15 entities).

### 5 — Tests

| Test | Requirement |
|------|-------------|
| `test_bootstrap_deferred_save_single_flush` | Lahman handler or synthetic loop: N `save_entity` calls → 1 disk write (mock `_atomic_write` / patch `open`) |
| `test_entity_minisql_v1_migration` | Grain crosses threshold → migrates → lookup/bind still works |
| `test_lahman_seed_handler_*` | Existing smoke tests green |
| CRM capstones / Program 2 matrix | Green |
| `test_multi_mvr_entity_stores` | Green |

### 6 — Docs

- `docs/architecture.md` addendum: entity store ownership; deferred bootstrap save; minisql reuse; per-grain migration.
- **Do not** edit `TODO.md`.

---

## Out of scope

- Query graph grain selection changes
- Removing JSON entity stores entirely
- Specialist storage changes (already slices 1–2)
- `mycelium query` baseball wiring

---

## Scope boundaries (strict)

**You may modify:**

- `src/agents/entity_registry.py` (delegate persistence; keep lookup/bind API)
- `src/storage/entity_store.py` or `src/agents/entity_store.py` (new — pick one, document)
- `src/storage/minisql_v1.py` (extend for entity grain shape — reuse slice 2 module)
- `src/network/bootstrap/run.py` (deferred-save wiring)
- `src/agents/attribute_write.py` (only if required for deferred-save integration with `save_entity`)
- `tests/test_lahman_seed_handler.py`, new entity-store tests, existing multi-grain / capstone tests as needed
- `docs/architecture.md` (minimal addendum only)

**Out of scope (do not touch):**

- `TODO.md` (Grok + Paul only)
- `src/agents/specialists/` storage (slices 1–2)
- Query graph / supervisor grain selection
- Baseball query orchestrator (separate track)

If changes outside this scope seem necessary: **stop**, document in `output.md`, do not implement.

---

## Success criteria

1. Bootstrap handlers flush entity store **once per grain** (deferred save).
2. Entity `minisql_v1` migration works via shared module.
3. Threshold gating per grain; CRM person grain unaffected at 15 entities.
4. `./bin/ci-local` green.
5. Lahman + CRM capstone tests green.

---

## Deliverables

Per `WORKFLOW.md`:

- `prompts/cursor/done/2026-06-17-2300-entity-registry-storage-evolution/prompt.md`
- `output.md` with verification counts + **For Grok + Paul**:
  - Note: Paul + Grok run **timing test 5** per `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`; compare to test 3
- Suggested commit message: `feat(entities): deferred bootstrap save and minisql_v1 entity store migration`
- **Do not commit or push**

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: timing test 5 gate; program completion notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-17-2300-entity-registry-storage-evolution/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul **"slice ready for review"**

---

## Release from HOLD

Paul or Grok moves this file to `prompts/cursor/next/` after **timing test 3** is recorded (`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` or slice 2 `review.md`).
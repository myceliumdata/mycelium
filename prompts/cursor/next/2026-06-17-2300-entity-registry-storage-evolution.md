# Entity registry storage — deferred bootstrap save + `minisql_v1`

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Program:** Storage evolution (specialist → entity). **Slice 4 of 5.** Map: `docs/plans/storage-evolution-program.md`

| Prerequisite | Status |
|--------------|--------|
| Slice 1 approved | `2026-06-17-1900-specialist-optimize-storage-check` |
| Slice 2 approved | `2026-06-17-2100-specialist-minisql-v1-migrate` |
| Timing test 3 | Paul recording (baseline **12,600 s / ~3.5 h** pre slice 2) |

**Context:** Baseball bootstrap slowness is dominated by **entity registry** I/O (`entities/team.json`, `entities/player.json`). `EntityRegistry._save()` rewrites the full JSON document on **every** `save_entity` — including each `ensure_entity_bind_fields` / `add_bind_alias` in `LahmanSeedHandler` (~tens of thousands of flushes per refresh). Slices 1–2 fixed specialist storage only. **This slice** extracts persistence into `EntityStore`, adds **deferred flush during bootstrap**, and optional per-grain `minisql_v1` migration at threshold.

**After this slice:** Paul + Grok run **timing test 5** (manual); compare to baseline and test 3.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| E1 | **Option C — store only:** `EntityStore` handles persistence; **`EntityRegistry` stays the public API** (`get_entity_registry()`, lookup/bind). **No** `IdentityAgent` / dispatch refactor in this slice. |
| E2 | **Post-baseball refactor (deferred):** After the **full baseball example** ships, evaluate moving registry ownership to an **identity agent** per grain. Document in architecture addendum; do not implement. |
| E3 | **`EntityStore` location:** `src/storage/entity_store.py` (alongside `minisql_v1.py`). |
| E4 | **Per-grain paths:** unchanged — `entities/<grain>.json` from `network.json` `mvr.grains`. |
| E5 | **Strategy file:** co-located `entities/<grain>.storage_strategy.json` (mirror specialist `storage_strategy.json` pattern). JSON strategy name: **`entities_document_v1`**. |
| E6 | **Reuse `minisql_v1`:** extend `src/storage/minisql_v1.py` with entity-document load/save/migrate — do not fork SQLite primitives. |
| E7 | **Threshold:** env `MYCELIUM_ENTITY_OPTIMIZE_STORAGE_THRESHOLD` (int, default **50**); fallback to `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD` when entity-specific unset. Per-grain evaluation. |
| E8 | **JSON backup on migrate:** rename `entities/<grain>.json` → `entities/<grain>.json.pre-minisql-v1` (do not delete). |
| E9 | **Bootstrap batching:** `run_network_bootstrap` wraps handler with deferred save — **one disk flush per grain** at end. Query-path `save_entity` still flushes immediately when not deferred. |
| E10 | **API unchanged:** all existing `EntityRegistry` methods and `get_entity_registry(grain=...)` behavior from caller view. |
| E11 | **CRM regression:** 15-entity CRM refresh, capstones, Program 2 matrix green. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/plans/storage-evolution-program.md`
- `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`
- `prompts/cursor/done/2026-06-17-2100-specialist-minisql-v1-migrate/`
- `src/agents/entity_registry.py` — `EntitiesDocument`, `_load`, `_save`, `save_entity`
- `src/storage/minisql_v1.py` — specialist payload shape (extend for entities)
- `src/network/bootstrap/run.py`
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`
- `tests/test_lahman_seed_handler.py`, `tests/test_multi_mvr_entity_stores.py`

---

## Architecture target

```
EntityRegistry (per grain) — framework API unchanged
    → EntityStore (src/storage/entity_store.py)
        → entities_document_v1 (JSON) OR minisql_v1 (SQLite)
    → _maybe_optimize_storage() before flush when entity_count >= threshold
        → EntityStore.migrate_to("minisql_v1")

Bootstrap (run_network_bootstrap):
    deferred_save context on each grain registry touched
        → in-memory mutations only
        → commit_deferred_save() once per grain at end of handler
```

**Entity SQLite file:** `entities/<grain>.sqlite` (same directory as JSON; document in architecture).

**Document shape** (`EntitiesDocument` in `entity_registry.py`):

```python
version, last_updated, entities: dict[str, RegistryEntity], bind_index: dict[str, str]
```

Entity minisql must round-trip this whole document (serialize `RegistryEntity` as JSON per row or one blob per entity — pick pragmatic v1; document choice).

---

## Implement

### 1 — `EntityStore` (`src/storage/entity_store.py`)

- Construct with `grain: str`, `json_path: Path`, `strategy_path: Path`, `sqlite_path: Path`
- `load() -> EntitiesDocument`
- `save(document: EntitiesDocument) -> None`
- `current_strategy() -> str`
- `migrate_to(target: str) -> None` for `entities_document_v1` → `minisql_v1`
- `entity_count() -> int` (len entities)
- Initialize strategy file when missing (same pattern as `SpecialistStorage._ensure_initialized`)

Refactor `EntityRegistry._load` / `_save` to delegate to `EntityStore`. Registry keeps `_data`, `_field_indexes`, all lookup/bind methods.

### 2 — Extend `minisql_v1.py` for entity documents

Add functions such as:

- `migrate_entities_document_v1_json(json_path, sqlite_path, *, grain: str) -> None`
- `load_entities_document(sqlite_path) -> dict` / `save_entities_document(sqlite_path, document: dict) -> None`

Must preserve `entities` + `bind_index` + `version` + `last_updated`. Reuse connection/schema helpers from specialist module where sensible (may add `entity_rows` / `bind_index_rows` tables or a single document blob table — v1 pragmatism OK).

### 3 — Deferred save for bootstrap

On `EntityRegistry`:

- `begin_deferred_save()` / `commit_deferred_save()` or context manager `deferred_save()`
- While deferred: update `_data` and indexes in memory; **skip** store flush
- `commit_deferred_save()` runs `_maybe_optimize_storage()` then single `save`

Wire in `run_network_bootstrap`:

```python
# Pseudocode — apply per grain registry used by handler
with registry.deferred_save():  # or explicit begin/commit wrapping handler.run
    result = handler.run(ctx)
```

`LahmanSeedHandler` uses `get_entity_registry(grain="team")` and `grain="player"` — bootstrap runner must defer **both** grains (e.g. module-level context stacking or defer all registries loaded during bootstrap). Document approach in `output.md`.

**Query path:** `save_entity` outside deferred mode still saves immediately.

### 4 — `optimize_storage` + migration on registry

On `EntityRegistry` (not a separate agent class):

```python
def optimize_storage_threshold(self) -> int: ...
def optimize_storage(self) -> bool:
    if self._store.current_strategy() != "entities_document_v1":
        return False
    return self.entity_count() >= self.optimize_storage_threshold()

def _maybe_optimize_storage(self) -> None:
    if not self.optimize_storage():
        return
    try:
        self._store.migrate_to("minisql_v1")
    except NotImplementedError:
        pass
```

Call `_maybe_optimize_storage()` before non-deferred `save` flushes.

### 5 — Multi-grain

Each grain has its own `EntityStore`, strategy file, and threshold. CRM `person` (15 entities) stays JSON; baseball `player` may migrate after threshold.

### 6 — Tests

| Test | Requirement |
|------|-------------|
| `test_bootstrap_deferred_save_single_flush` | N `save_entity` calls under deferred → 1 disk write (spy `EntityStore.save` or patch atomic write) |
| `test_entity_minisql_v1_migration` | Cross threshold → migrate → lookup/bind/index still work |
| `test_entity_minisql_v1_json_backup` | Backup file exists; strategy updated |
| `test_lahman_seed_handler_*` | Existing smoke green |
| `test_multi_mvr_entity_stores` | Green |
| CRM capstones / Program 2 matrix | Green |

Use `@pytest.mark.smoke` on new tests.

### 7 — Docs (`docs/architecture.md` minimal addendum)

- `EntityStore` framework ownership (Option C)
- Deferred bootstrap save; per-grain minisql; strategy/backup paths
- **Deferred program note:** identity-agent refactor planned **after full baseball example** ships — not this slice

**Do not** edit `TODO.md`.

---

## Out of scope

- `IdentityAgent` / protocol dispatch / renaming `get_entity_registry`
- Query graph grain selection / baseball query orchestrator
- Specialist storage (slices 1–2)
- Removing JSON entity backends entirely
- Lahman handler algorithm changes (only benefit from deferred flush)

---

## Scope boundaries (strict)

**You may modify:**

- `src/storage/entity_store.py` (new)
- `src/storage/minisql_v1.py` (entity document adapter)
- `src/agents/entity_registry.py` (delegate persistence; deferred save; optimize hook)
- `src/network/bootstrap/run.py` (deferred-save wiring)
- `src/agents/attribute_write.py` (only if required for deferred-save correctness)
- Tests listed above + `docs/architecture.md` addendum

**Out of scope (do not touch):**

- `TODO.md`
- `src/agents/specialists/`
- Supervisor / `target_resolve` / query graph
- Bootstrap handler business logic in `lahman_seed.py` unless a one-line defer hook is unavoidable

If changes outside this scope seem necessary: **stop**, document in `output.md`, do not implement.

---

## Success criteria

1. Bootstrap: **one flush per grain** (deferred save), proven by test.
2. Entity `minisql_v1` migration + JSON backup works; lookup/bind/index correct post-migrate.
3. Threshold per grain; CRM person grain unchanged at 15 entities.
4. `./bin/ci-local` green.
5. Lahman + multi-grain + capstone tests green.

---

## Deliverables

Per `WORKFLOW.md`:

- `prompts/cursor/done/2026-06-17-2300-entity-registry-storage-evolution/prompt.md`
- `output.md` with verification counts + **For Grok + Paul**:
  - Timing test 5 command; compare to baseline (12,600 s) and test 3 when recorded
  - Note: storage evolution program complete after slice 5 gate
- Suggested commit message: `feat(entities): deferred bootstrap save and minisql_v1 entity store migration`
- **Do not commit or push**

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: timing test 5; post-baseball identity-agent refactor remains deferred.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-17-2300-entity-registry-storage-evolution/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul **"slice ready for review"**
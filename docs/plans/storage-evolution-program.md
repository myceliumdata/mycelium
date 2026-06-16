# Storage evolution program — specialist → entity (June 2026)

**Status:** **Code slices complete** (1, 2, 4, incremental writes, bootstrap progress UX). **Timing gate:** test 6 pending (Paul).  
**Motivation:** Baseball-scale bootstrap (`LahmanSeedHandler`) exposed quadratic save cost on every bind.  
**Prerequisite shipped:** [`SpecialistAgent` class](../architecture.md) — `prompts/cursor/done/2026-06-17-1800-specialist-agent-class/` (Approved 2026-06-17)  
**Timing gates:** [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../manual-checks/2026-06-17-storage-evolution-timing-gates.md)

---

## Problem (original framing)

| Layer | Symptom | Root cause (at program start) |
|-------|---------|-------------------------------|
| **Specialist storage** | Slow writes at research/bootstrap scale | `SpecialistStorage.save()` rewrites full `agents/<cat>/storage.json` on every `write_fields` |
| **Entity registry** | ~58k `_save()` calls during Lahman bootstrap | `EntityRegistry.save_entity()` → `_save()` flushes entire `entities/<grain>.json` per row |

---

## Post-mortem (June 2026 — after test 5 analysis)

Full detail: [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../manual-checks/2026-06-17-storage-evolution-timing-gates.md) § Lessons learned.

| Slice | Shipped | Wall-clock impact (Lahman) | Why |
|-------|---------|----------------------------|-----|
| **1** Threshold policy | Yes | None alone | Migration hook only |
| **2** Specialist `minisql_v1` | Yes | **Modest at best** | SQLite backend but **full-table replace** per `save_payload` — same O(n²) semantics as JSON file rewrite |
| **4** Entity `EntityStore` + deferred flush | Yes | **~No gain vs baseline** (~4.5 h est. vs ~3.5 h baseline) | Removed per-row entity **disk** flush; added per-row **in-memory** `_rebuild_field_indexes()` on every `save_entity` / `add_bind_alias` (~58k×). Specialists still dominated. |
| **Incremental specialist** (`c5e5bce`) | Yes | **Expected large** (test 6) | Per-entity upsert on hot path — fixes real O(n²) across categories |
| **Bootstrap progress** (`9052f45`) | Yes | UX only | stderr phases; no perf change |

**Process lesson:** Slice 2 review listed full-table `save_payload` as non-blocking follow-up; should have been **queued before** timing test 3/5. Program doc overstated slice 4 as “primary baseball perf slice” without incremental specialists.

**Follow-up (optional):** alias-only `add_bind_alias` — update `bind_index` without `_rebuild_field_indexes()`; entity `save_entities_document` full replace on bulk flush (separate from specialist incremental).

---

## Slice map

| # | Owner | Prompt / commit | Scope | Status |
|---|-------|-----------------|-------|--------|
| **1** | Cursor | `2026-06-17-1900-specialist-optimize-storage-check` | Threshold `optimize_storage()` on base `SpecialistAgent` | Approved |
| **2** | Cursor | `2026-06-17-2100-specialist-minisql-v1-migrate` (`179e80d`) | `migrate_to("minisql_v1")` + `src/storage/minisql_v1.py` | Approved |
| **3** | Paul + Grok | — | Timing test 3 | Estimate only — unreliable |
| **4** | Cursor | `2026-06-17-2300-entity-registry-storage-evolution` (`c898036`) | `EntityStore`; deferred bootstrap save; entity `minisql_v1` | Approved |
| **5** | Paul + Grok | — | Timing test 5 | Abandoned ~4.5 h est.; no gain |
| **—** | Cursor | `2026-06-17-2340-specialist-minisql-incremental-writes` (`c5e5bce`) | Per-entity specialist upsert (perf fix) | Approved |
| **—** | Cursor | `2026-06-17-2355-bootstrap-progress-reporting` (`9052f45`) | stderr bootstrap progress | Approved |
| **6** | Paul + Grok | — | Timing test 6 post-`c5e5bce` | **Pending** |

**Queue index:** `prompts/cursor/HOLD.md`

---

## Locked decisions (program-wide)

| # | Decision |
|---|----------|
| P1 | **Strategy name:** `minisql_v1` for SQLite backends (matches `storage_strategy.json` `next_candidates`). |
| P2 | **Threshold default:** 50 records (`MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD`; entity slice may add `MYCELIUM_ENTITY_OPTIMIZE_STORAGE_THRESHOLD` or document shared knob). |
| P3 | **Per-instance / per-grain isolation:** each specialist category and each entity grain evaluates its own count independently. |
| P4 | **Cheap guard first:** if `current_strategy()` is not the JSON strategy, skip `record_count()` / `entity_count()`. |
| P5 | **JSON backup on migrate:** rename source JSON → `*.pre-minisql-v1`; do not delete. |
| P6 | **Protocol/API unchanged:** `read_fields` / `write_fields`, lookup/bind, admin snapshots same shapes post-migration. |
| P7 | **CRM regression:** 15-entity CRM refresh, capstones, Program 2 matrix stay green throughout. |
| P8 | **Shared SQLite module:** `src/storage/minisql_v1.py` — specialist and entity stores. |
| P9 | **Specialist hot path (June 2026):** per-entity `load_entity` / `save_entity` on `minisql_v1`; bulk `save_payload` for migration only. |

---

## Architecture target (end state — achieved in code)

```
SpecialistAgent.write_fields / bootstrap_entity
    → _maybe_optimize_storage() [threshold on base class]
        → SpecialistStorage.migrate_to("minisql_v1")
            → storage/minisql_v1.py
    → minisql_v1 hot path: load_entity + upsert_entity_record (one entity per bind)

EntityRegistry.save_entity (query path)
    → optimize_storage() [per grain]
        → EntityStore.migrate_to("minisql_v1")
            → storage/minisql_v1.py (shared)

Bootstrap (LahmanSeedHandler, DefaultSeedHandler)
    → bootstrap_deferred_save(before_commit=progress.cleaning_up)
        → in-memory mutations; _rebuild_field_indexes per save (follow-up: alias skip)
        → one flush per grain at commit
```

---

## Out of program scope

- Query graph grain selection / baseball query orchestrator (separate baseball program track in `TODO.md`)
- Removing JSON storage backends entirely (both JSON and SQLite coexist)
- Full relational normalization of versioned field blobs (v1 stores JSON text per key; optimize I/O first)
- Unifying graph `get_specialist_storage()` with `AGENT.storage` (review nit N1 — follow-up)
- **`IdentityAgent` / identity specialist** — deferred until **full baseball example** ships; then evaluate refactor against live data/behavior baseline (Paul, June 2026)
- Skip index rebuild on alias-only `add_bind_alias` (optional follow-up slice)

---

## Review / commit policy

Per `prompts/cursor/WORKFLOW.md`: Grok reviews each slice, runs `./bin/ci-local`, commits locally on **Approved**; Paul pushes `origin` when the program (or agreed milestone) is ready.

---

*Last updated: 2026-06-17 (Grok — post-mortem after test 5 analysis; test 6 pending)*
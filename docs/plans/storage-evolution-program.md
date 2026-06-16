# Storage evolution program — specialist → entity (June 2026)

**Status:** **Active** — slices 1–2 shipped; slice 4 in `prompts/cursor/next/`
**Motivation:** Baseball-scale bootstrap (`LahmanSeedHandler`) exposed O(n) JSON rewrite cost on every save. Specialist category storage and per-grain entity stores both need threshold-gated migration to **`minisql_v1`** (SQLite) plus bootstrap-friendly batch persistence for entity grains.  
**Prerequisite shipped:** [`SpecialistAgent` class](../architecture.md) — `prompts/cursor/done/2026-06-17-1800-specialist-agent-class/` (Approved 2026-06-17)  
**Timing gates:** [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../manual-checks/2026-06-17-storage-evolution-timing-gates.md)

---

## Problem (two bottlenecks)

| Layer | Symptom | Root cause today |
|-------|---------|------------------|
| **Specialist storage** | Slow writes at research/bootstrap scale | `SpecialistStorage.save()` rewrites full `agents/<cat>/storage.json` on every `write_fields` |
| **Entity registry** | ~58k `_save()` calls during Lahman bootstrap | `EntityRegistry.save_entity()` → `_save()` flushes entire `entities/<grain>.json` per row |

Specialist evolution (slices 1–2) does **not** fix entity I/O. Entity evolution (slice 4) does **not** replace specialist work — both are required for baseball refresh perf.

---

## Slice map

| # | Owner | Prompt | Scope |
|---|-------|--------|-------|
| **1** | Cursor | `prompts/cursor/next/2026-06-17-1900-specialist-optimize-storage-check.md` | Threshold `optimize_storage()` on base `SpecialistAgent` (policy only; migration still no-op) |
| **2** | Cursor | `prompts/cursor/next/2026-06-17-2100-specialist-minisql-v1-migrate.md` | Implement `migrate_to("minisql_v1")` + shared `src/storage/minisql_v1.py` |
| **3** | Paul + Grok | — | **Timing test 3** after slice 2 approved; record baseline in manual-check doc |
| **4** | Cursor | `prompts/cursor/next/2026-06-17-2300-entity-registry-storage-evolution.md` | **Option C:** `EntityStore` + `EntityRegistry` API unchanged; deferred bootstrap save; entity `minisql_v1` |
| **5** | Paul + Grok | — | **Timing test 5** after slice 4 approved; compare to test 3 |

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
| P8 | **Shared SQLite module:** `src/storage/minisql_v1.py` — specialist slice 2 creates; entity slice 4 reuses. |

---

## Architecture target (end state)

```
SpecialistAgent.write_fields / bootstrap_entity
    → _maybe_optimize_storage() [threshold on base class]
        → SpecialistStorage.migrate_to("minisql_v1")
            → storage/minisql_v1.py

EntityRegistry.save_entity (query path)
    → optimize_storage() [per grain]
        → EntityStore.migrate_to("minisql_v1")
            → storage/minisql_v1.py (shared)

Bootstrap (LahmanSeedHandler, DefaultSeedHandler)
    → deferred_save on registry
        → one flush per grain at commit
```

---

## Out of program scope

- Query graph grain selection / baseball query orchestrator (separate baseball program track in `TODO.md`)
- Removing JSON storage backends entirely (both JSON and SQLite coexist)
- Full relational normalization of versioned field blobs (v1 stores JSON text per key; optimize I/O first)
- Unifying graph `get_specialist_storage()` with `AGENT.storage` (review nit N1 — follow-up)
- **`IdentityAgent` / identity specialist** — deferred until **full baseball example** ships; then evaluate refactor against live data/behavior baseline (Paul, June 2026)

---

## Review / commit policy

Per `prompts/cursor/WORKFLOW.md`: Grok reviews each slice, runs `./bin/ci-local`, commits locally on **Approved**; Paul pushes `origin` when the program (or agreed milestone) is ready.

---

*Last updated: 2026-06-17 (Grok — queue prep after SpecialistAgent approval)*
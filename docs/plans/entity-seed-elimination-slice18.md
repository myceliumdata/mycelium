# Seed elimination — Slice 18: Admin UI + docs + phase exit

**Status:** Ready (June 2026)  
**Depends on:** Slice 17 (seed module deleted)  
**Phase map:** [`entity-seed-elimination-phase.md`](entity-seed-elimination-phase.md)

---

## Objective

Operator surfaces show **Entities** (registry count), not Seed. Phase exit: **full pytest green**.

---

## Admin UI (`admin-ui/`)

- **`App.tsx`**: Remove `Seed ({status.seed_people_count})` line. Overview shows **Entities** count from `registry_entity_count` only (drop separate Registry line if redundant).
- **`types.ts`**: Remove `seed_people_count` from `StatusResponse`.

Rebuild not required in prompt deliverable; note if `dist/` is committed.

---

## API / introspection (already partially done)

- `NetworkStatusSummary.registry_entity_count` is canonical.
- Remove `seed_people_count` from JSON if still present anywhere.
- CLI demo format: `Entities: ✅ (N)` not `Seed:`.

---

## Tests to update

- `tests/test_admin_daemon.py` — `registry_entity_count`; entities.json hot-reload test (not seed.json).
- `tests/test_network_status.py` — same.
- `tests/test_network_polish.py` — remove/replace `test_missing_seed_raises_file_not_found` (seed optional at runtime).

---

## Docs (task-scoped)

- **`README.md`**: admin/status examples use `registry_entity_count`; note seed is bootstrap-only via refresh/create.
- **`docs/architecture.md`**: seed loader section → bootstrap import + registry resolution.
- **`docs/plans/entity-seed-elimination-phase.md`**: check exit criteria boxes.

---

## Phase exit (mandatory)

```bash
uv run ruff check src tests
uv run pytest -q
```

All tests green before marking phase complete in `output.md`.

---

## Out of scope

- Historical prompts under `prompts/cursor/done/`.
- `TODO.md` (Grok + Paul).
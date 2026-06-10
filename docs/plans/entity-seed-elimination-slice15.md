# Seed elimination — Slice 15: Registry-only resolution

**Status:** Ready (June 2026)  
**Depends on:** Slice 14 (bootstrap import)  
**Phase map:** [`entity-seed-elimination-phase.md`](entity-seed-elimination-phase.md)

---

## Objective

All entity lookup at query time goes through **`entities.json`** (via `EntityRegistry`). Remove the seed branch from resolution.

---

## `src/agents/entity_resolution.py`

- `resolve_entity` / `resolve_entity_for_lookup`: registry only (by UUID, bind key, name).
- Near-miss **suggestions** scan `registry.list_entities()` (not seed file).
- Add or consolidate **`lookup_entities_by_key(entity_key) -> list[dict]`** — public helper used by routing, dispatch, introspection, tests.
- Match dicts use `registry_entity_to_match` (`_registry: True`, `_validation_state`).

**Lookup order (unchanged semantics, registry source):**

1. UUID-shaped key → `lookup_by_id`
2. Exact bind match (MVR) → registry bind index
3. Name match (0..N)
4. Suggest → unknown / under_specified / bind_provisional

---

## Call site updates

- `src/agents/routing.py`, `src/agents/dispatch.py` — use `lookup_entities_by_key` (no `agents.seed`).
- `src/network/introspection.py` — entity drill-down via registry helper.
- Remove any `find_by_key` / `get_seed_data` imports in `src/`.

---

## Tests

- Existing entity protocol tests: fixtures must **`import_seed_file`** (or `import_seed_at_root`) after copying `seed.json`, not `get_seed_data`.
- `lookup_entities_by_key("Andrea Kalmans")` works when entities imported.
- Empty registry (no seed import): Paul Murphy bind arc still works via `query_bind`.

---

## Out of scope

- Deleting `agents/seed.py` (Slice 17) — but stop **calling** it from resolution in this slice.
- Context builder / runtime reload (Slice 16).
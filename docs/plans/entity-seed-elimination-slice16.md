# Seed elimination — Slice 16: Context + runtime

**Status:** Ready (June 2026)  
**Depends on:** Slice 15 (registry-only resolution)  
**Phase map:** [`entity-seed-elimination-phase.md`](entity-seed-elimination-phase.md)

---

## Objective

Remove seed from context assembly and long-lived runtime refresh paths. All matched rows are registry rows.

---

## `src/agents/context.py`

- `_resolve_identity_rows` (or equivalent): load bind fields from **registry by id**, not seed.
- `ContextBuilder` constructor / params: drop seed-specific `identity_records` from seed loader; use registry lookups for matched ids.

---

## `src/agents/runtime.py`

- `refresh_runtime_from_disk`: remove `reset_seed_data()` / `get_seed_data()`.
- Keep `reset_entity_registry()` so MCP/admin see on-disk `entities.json` after refresh.

---

## `src/agents/research_gate.py`

- All matches are registry rows; gating uses `validation_state == "validated"` (seed bootstrap rows are pre-validated).

---

## `src/mycelium_admin/server.py`

- `_refresh_read_cache`: `reset_entity_registry()` only (no seed reset).
- Bootstrap: no seed loader warm.

---

## `src/agents/supervisor.py`

- Audit log source: `"registry"` for all exact matches (remove seed branch in source detection if still present).

---

## Tests

- `tests/test_mcp_runtime_reload.py`: entity id stable across `refresh_runtime_from_disk` when `entities.json` persisted (not seed reload).
- Admin `/status` reflects `entities.json` changes after registry reset (not live `seed.json` edits).

---

## Out of scope

- Delete `agents/seed.py` (Slice 17).
- Admin UI label changes (Slice 18).
# Task: Seed elimination — Slice 15 (registry-only resolution)

> **READY** — Move to `in-progress/` before starting. **Run after Slice 14 is reviewed.**

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-seed-elimination-slice15.md`](../../docs/plans/entity-seed-elimination-slice15.md) — **locked spec**

**Depends on:** Slice 14 (bootstrap import).

---

## Objective

Entity resolution at query time uses **`entities.json` only**. Remove seed branch from `resolve_entity` / suggestions. Expose `lookup_entities_by_key` for callers.

---

## Implement

### 1 — `src/agents/entity_resolution.py`

- Registry-only resolution (UUID, bind, name, suggest, unknown, bind_provisional).
- Suggestions from `registry.list_entities()`.
- `lookup_entities_by_key(entity_key) -> list[dict]` using `registry_entity_to_match`.

### 2 — Call sites

Update to use `lookup_entities_by_key` (no `agents.seed`):
- `src/agents/routing.py`
- `src/agents/dispatch.py`
- `src/network/introspection.py` (entity drill-down)

### 3 — Tests

Entity protocol tests that copy `seed.json` must **import into registry** in fixtures:
- Use `network.seed_import.import_seed_file` or `tests/network_helpers.import_seed_for_test`
- Set `MYCELIUM_ENTITIES_PATH` / `MYCELIUM_NETWORK_ROOT` as needed

Do **not** call `get_seed_data()` for resolution tests.

Smoke tests for suggestions, unknown MVR, registry bind — run affected files.

---

## Scope boundaries (strict)

**May modify:**
- `src/agents/entity_resolution.py`
- `src/agents/routing.py`
- `src/agents/dispatch.py`
- `src/network/introspection.py`
- `tests/test_entity_*.py`, `tests/test_network_status.py`, `tests/network_helpers.py` (fixture import only)

**Out of scope:**
- Delete `agents/seed.py` (Slice 17)
- Context, runtime, admin UI
- `TODO.md`

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **No commit before review.**

---

## Deliverables

`prompts/cursor/done/2026-06-10-1500-entity-seed-elimination-slice15/` with `prompt.md`, `output.md`.

---

## Verify

```bash
uv run ruff check src/agents/entity_resolution.py src/agents/routing.py src/agents/dispatch.py
uv run pytest tests/test_entity_key_suggestions.py tests/test_entity_unknown_mvr.py tests/test_entity_registry_bind.py tests/test_network_status.py -m smoke -q
```
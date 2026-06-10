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

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: slice status, follow-on notes, suggested commit message.
- **No commit or push before review.** Leave changes in the working tree only.

### Stay in your lane (Cursor)

You are the **implementer**, not the reviewer or planner. Slice 14 incorrectly drafted `review.md` as Grok — do **not** repeat that.

- **Deliver only:** code, tests (within scope), `prompt.md` + `output.md` under `prompts/cursor/done/<this-task>/`.
- **Do not create** `review.md` — review is **Grok + Paul only** (`prompts/cursor/WORKFLOW.md` §4).
- **Do not** edit `TODO.md`, mark slices shipped in plan docs, queue new prompts, or expand scope into later slices (16–18).
- **Do not** delete `agents/seed.py` or touch context/runtime/admin — that is Slice 16–17.
- If you must go outside scope to keep the system working: **stop**, document in `output.md`, do not make the out-of-scope changes.

---

## Deliverables

`prompts/cursor/done/2026-06-10-1500-entity-seed-elimination-slice15/` with `prompt.md` and `output.md` **only** (no `review.md`).

---

## Verify

```bash
uv run ruff check src/agents/entity_resolution.py src/agents/routing.py src/agents/dispatch.py
uv run pytest tests/test_entity_key_suggestions.py tests/test_entity_unknown_mvr.py tests/test_entity_registry_bind.py tests/test_network_status.py -m smoke -q
```
# Task: Seed elimination — Slice 16 (context + runtime)

> **READY** — Move to `in-progress/` before starting. **Run after Slice 15 is reviewed.**

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-seed-elimination-slice16.md`](../../docs/plans/entity-seed-elimination-slice16.md) — **locked spec**

**Depends on:** Slice 15 (registry-only resolution).

---

## Objective

Remove seed from context assembly and MCP/admin runtime refresh. Matched rows are always registry rows.

---

## Implement

### 1 — `src/agents/context.py`

- Identity/bind rows resolved from registry by id (not seed loader).
- Drop seed-specific identity record plumbing.

### 2 — `src/agents/runtime.py`

- `refresh_runtime_from_disk`: remove `reset_seed_data()` / `get_seed_data()`.
- Keep `reset_entity_registry()` so on-disk `entities.json` reloads.

### 3 — `src/agents/research_gate.py`

- Gating on registry `validation_state` (validated bootstrap rows pass).

### 4 — `src/mycelium_admin/server.py`

- `_refresh_read_cache`: `reset_entity_registry()` only.

### 5 — `src/agents/supervisor.py`

- Audit log: exact matches report `resolved via registry` (no seed source branch).

### 6 — Tests

- `tests/test_mcp_runtime_reload.py` — stable ids across refresh via persisted `entities.json`
- `tests/test_entity_research_gate.py`, `tests/test_entity_boundary.py`, `tests/test_admin_daemon.py` (runtime paths)
- `tests/test_supervisor_routing.py` — registry resolution wording

---

## Scope boundaries (strict)

**May modify:**
- `src/agents/context.py`
- `src/agents/runtime.py`
- `src/agents/research_gate.py`
- `src/mycelium_admin/server.py`
- `src/agents/supervisor.py`
- Tests listed above

**Out of scope:**
- Delete `agents/seed.py` (Slice 17)
- Admin UI labels (Slice 18)
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
- **Do not** edit `TODO.md`, mark slices shipped in plan docs, queue new prompts, or expand scope into Slice 17–18 work.
- **Do not** delete `agents/seed.py` or sweep all tests for seed imports — that is Slice 17.
- If you must go outside scope to keep the system working: **stop**, document in `output.md`, do not make the out-of-scope changes.

---

## Deliverables

`prompts/cursor/done/2026-06-10-1600-entity-seed-elimination-slice16/` with `prompt.md` and `output.md` **only** (no `review.md`).

---

## Verify

```bash
uv run pytest tests/test_mcp_runtime_reload.py tests/test_entity_research_gate.py tests/test_supervisor_routing.py -m smoke -q
```
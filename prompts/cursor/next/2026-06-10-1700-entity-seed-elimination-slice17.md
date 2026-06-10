# Task: Seed elimination — Slice 17 (delete runtime seed module)

> **READY** — Move to `in-progress/` before starting. **Run after Slice 16 is reviewed.**

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-seed-elimination-slice17.md`](../../docs/plans/entity-seed-elimination-slice17.md) — **locked spec**

**Depends on:** Slice 16 (no runtime seed reads).

---

## Objective

Delete `agents/seed.py` and legacy `mycelium seed` CLI. Tests use `import_seed_file` / `import_seed_at_root` helpers only. Fix broken test fixtures from bulk edits.

---

## Implement

### 1 — Delete `src/agents/seed.py`

Confirm `rg 'agents\.seed'` in `src/` is clean after deletion.

### 2 — `src/main.py`

- Remove `seed` subcommand (parser + handler).
- Update any help text that references `agents.seed`.

### 3 — `src/storage/core.py`

- Docstring: identity via `entities.json`, not seed loader.
- Decouple `seed_from_file` from seed module; tests use `import_seed_file` for CRM identity.

### 4 — Test helpers — `tests/network_helpers.py`

- `import_seed_for_test`, `import_seed_at_root` per spec.

### 5 — Test sweep

Replace all `agents.seed` / `get_seed_data` / `reset_seed_data` / `find_by_key` imports in `tests/`.

**Fix indentation errors** where `reset_seed_data()` was removed leaving over-indented lines (e.g. `        reset_context_builder()` → `    reset_context_builder()`).

Update `tests/conftest.py` session cleanup: `reset_entity_registry` not `reset_seed_data`.

### 6 — `tests/test_network_integration.py`

`_reset_runtime_singletons`: include `reset_entity_registry`, no seed reset.

---

## Scope boundaries (strict)

**May modify:**
- `src/agents/seed.py` (delete)
- `src/main.py`
- `src/storage/core.py`
- `tests/**` (broad — seed import migration)
- `tests/conftest.py`
- `tests/network_helpers.py`

**Out of scope:**
- Admin UI / README (Slice 18)
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
- **Do not** edit `TODO.md`, mark the phase complete in plan docs, or queue new prompts.
- **Do not** touch admin UI, README, or architecture — that is Slice 18.
- Fix only test/seed migration within this slice; do not "finish the phase" in one pass.
- If you must go outside scope to keep the system working: **stop**, document in `output.md`, do not make the out-of-scope changes.

---

## Deliverables

`prompts/cursor/done/2026-06-10-1700-entity-seed-elimination-slice17/` with `prompt.md` and `output.md` **only** (no `review.md`).

---

## Verify

```bash
rg 'agents\.seed|get_seed_data|reset_seed_data' src/ tests/
uv run ruff check src tests
uv run pytest -m smoke -q
```

Report any remaining smoke failures in `output.md` for Slice 18.
# Task: Seed elimination — Slice 14 (bootstrap import)

> **READY** — Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-seed-elimination-slice14.md`](../../docs/plans/entity-seed-elimination-slice14.md) — **locked spec**
- [`docs/plans/entity-seed-elimination-phase.md`](../../docs/plans/entity-seed-elimination-phase.md) — phase context

**Depends on:** Slice 13 shipped (`ensure_bound_entity`, uuid4).

**Note:** Partial WIP may exist on the branch (e.g. `src/network/seed_import.py`). Reconcile against this spec; do not assume it is complete or correct.

---

## Objective

Import `seed.json` into `entities.json` **only at bootstrap** when the file exists. `refresh-example-network` and `network create` are the triggers. Query time must **not** read seed yet (Slices 15–17).

---

## Implement

### 1 — `src/network/seed_import.py`

Implement `import_seed_file` per spec:
- Missing file → return `0`
- Each person row → `ensure_bound_entity(..., source="seed_bootstrap", validation_state="validated")`
- Idempotent via `bind_index`

### 2 — `src/network/example.py`

After copy/wipe in `refresh_example_network`, when `live_root / "seed.json"` exists:
```python
import_seed_file(seed_path)
```

### 3 — `src/network/create.py`

After copying optional `--seed` file to `paths.seed_path`, call `import_seed_file(paths.seed_path)`.

### 4 — Tests (smoke)

- Refresh CRM example → `entities.json` with 15 entities
- `import_seed_file` idempotency
- Missing seed path → `0`

Add `@pytest.mark.smoke` as appropriate.

---

## Scope boundaries (strict)

**May modify:**
- `src/network/seed_import.py`
- `src/network/example.py`
- `src/network/create.py`
- `tests/test_example_network.py`
- `tests/test_network_create.py` (import assertions only)

**Out of scope:**
- `agents/seed.py`, resolution, context, runtime, admin UI
- `TODO.md`

If resolution/runtime changes seem required, **stop** and document in `output.md`.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, add **"For Grok + Paul"**: slice status, follow-on notes.
- **No commit before review.**

---

## Deliverables

Move this file to `prompts/cursor/done/2026-06-10-1400-entity-seed-elimination-slice14/` as `prompt.md` and write `output.md`.

---

## Verify

```bash
uv run ruff check src/network/seed_import.py src/network/example.py src/network/create.py
uv run pytest tests/test_example_network.py tests/test_network_create.py -m smoke -q
```
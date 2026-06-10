# Task: Seed elimination — Slice 15 fix (supervisor routing smoke)

> **READY** — **Run before Slice 16.** Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- Slice 15 review: `prompts/cursor/done/2026-06-10-1500-entity-seed-elimination-slice15/review.md` — **blocking items**
- Slice 15 output: `prompts/cursor/done/2026-06-10-1500-entity-seed-elimination-slice15/output.md`

**Context:** Slice 15 (registry-only resolution) is in the working tree, **not yet committed**. This fix completes Slice 15 sign-off. Do **not** revert Slice 15 changes.

**Depends on:** Slice 15 WIP (registry-only `resolve_entity`).

---

## Objective

Repair **full smoke** failures in `tests/test_supervisor_routing.py` caused by Slice 15. `supervisor_agent` resolves via `resolve_entity` → registry only. Three tests still assume seed-json runtime lookup without importing into `entities.json`.

---

## Problem (from review)

After Slice 15, with an isolated env:

- Tests that write `seed.json` but skip `import_seed_for_test` get `unknown` / no match.
- `test_supervisor_agent_plans_no_specialists_without_attrs` asserts `"resolved via seed"` — stale.
- Full suite (`uv run pytest -m smoke -q`): **3 failures** in `test_supervisor_routing.py` (order-dependent without proper registry isolation).

---

## Implement

### 1 — Shared fixture helper (preferred)

Add a small helper or fixture in `tests/test_supervisor_routing.py` (or reuse `network_helpers.import_seed_for_test`) that:

1. Sets `MYCELIUM_NETWORK_ROOT` and `MYCELIUM_ENTITIES_PATH` under `tmp_path`
2. Writes `seed.json` with the test person row(s)
3. Calls `reset_entity_registry()` then `import_seed_for_test(seed)`
4. Optionally sets `MYCELIUM_SEED_PATH` if still needed by other resets in the test

Use this in all three failing supervisor integration tests.

### 2 — Fix three tests

| Test | Fix |
|------|-----|
| `test_supervisor_agent_plans_no_specialists_without_attrs` | Import seed into registry; assert **`resolved via registry`** (not seed); update docstring |
| `test_supervisor_agent_classifies_requested_attributes` | Isolated registry with imported `any-key` row so specialists plan deterministically |
| `test_supervisor_triggers_creation_for_unregistered_specialist` | Same — registry must contain `any-key` before `supervisor_agent` runs |

Do **not** change `src/agents/supervisor.py` audit wording in this fix (Slice 16 may update supervisor seed/registry messaging). Tests should match current `"resolved via registry"` string.

### 3 — Isolation

Ensure these tests do **not** depend on host `data/entities.json` pollution. Each must use its own `tmp_path` entities file and `reset_entity_registry()` in setup.

---

## Scope boundaries (strict)

**May modify:**
- `tests/test_supervisor_routing.py` only

**Out of scope:**
- `src/agents/*` (including supervisor, resolution, research_gate)
- Slice 16+ work
- `TODO.md`
- Committing Slice 15 (Grok + Paul after fix is reviewed)

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, add **"For Grok + Paul"**: confirm full smoke green; Slice 15 ready to commit with this fix.
- **No commit or push before review.**

### Stay in your lane (Cursor)

- **Deliver only:** `tests/test_supervisor_routing.py`, `prompt.md`, `output.md`.
- **Do not create** `review.md`.
- **Do not** start Slice 16 or touch context/runtime/seed deletion.

---

## Verify (mandatory)

```bash
uv run pytest tests/test_supervisor_routing.py -m smoke -q
uv run pytest -m smoke -q
```

**Exit gate:** full smoke **0 failures**. Report counts in `output.md`.

---

## Deliverables

`prompts/cursor/done/2026-06-10-1545-entity-seed-elimination-slice15-fix/` with `prompt.md` and `output.md` **only**.

---

## Suggested commit message (for Grok + Paul after review)

```
Fix supervisor routing tests for registry-only resolution (Slice 15 fix).

Import seed into entities.json in supervisor integration tests;
assert resolved via registry. Full smoke green.
```

Note in `output.md`: Paul should commit **Slice 15 + this fix** together (or as stacked commits) after review.
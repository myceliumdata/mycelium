# Task: Entity ID unification — Slice 13 (uuid4 everywhere)

> **READY** — Seed elimination step 1. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-uuid4-unification-slice13.md`](../../docs/plans/entity-uuid4-unification-slice13.md) — **locked spec**

**Depends on:** Entity program Slices 1–12 shipped.

---

## Objective

Unify entity ID allocation on **uuid4** with **`entities.json` `bind_index` as persistence**. Remove seed `uuid5`. Do **not** remove runtime seed resolution yet.

---

## Critical constraint

MCP calls `refresh_runtime_from_disk()` before each query → `reset_seed_data()` + reload seed. uuid4 without registry persistence **breaks specialist storage keys**. Seed enrich **must** call registry `ensure_bound_entity` so reload reuses ids.

Also add `reset_entity_registry()` to `refresh_runtime_from_disk` (before seed reload) so enrich reads on-disk `entities.json`.

---

## Implement (in order)

### 1 — `EntityRegistry.ensure_bound_entity`

In `src/agents/entity_registry.py`:

- New method per spec (uuid4 on miss, bind_index reuse on hit)
- Refactor `bind_provisional` to use it
- Preserve existing duplicate-bind / promotion behavior

### 2 — Seed loader

In `src/agents/seed.py`:

- Delete uuid5 (`_ID_NAMESPACE`, `_ID_PREFIX`, uuid5 in `_assign_id`)
- `_enrich_person` → `ensure_bound_entity(..., source="seed_bootstrap", validation_state="validated")`
- Update module docstring

### 3 — `storage/core.py`

- Stop importing uuid5 `_assign_id` for divergent behavior
- Align `seed_from_file` with registry helper

### 4 — MCP runtime refresh

In `src/agents/runtime.py` `refresh_runtime_from_disk`:

- `reset_entity_registry()` then registry reload (via next `get_entity_registry()` or explicit)
- Keep existing seed reset/reload order **after** registry reset

### 5 — Tests

- Unit tests for `ensure_bound_entity`
- **MCP stability test:** persist `entities.json`, `reset_seed_data()` twice, same id for same person
- Fix tests/docs that assume seed hits skip `entities.json`
- Run: `uv run pytest tests/test_entity_registry_bind.py tests/test_entity_growth.py tests/test_entity_validation.py tests/test_entity_unknown_mvr.py -q`
- Run: `uv run pytest -m smoke -q`

### 6 — Docs

- `docs/architecture.md`, `docs/full-code-walkthrough.md`, seed module docstring
- Add Slice 13 row to `docs/plans/entity-protocol-and-registry-program.md` slice map

---

## Governance

- **Do not edit `TODO.md`**
- No seed elimination beyond uuid unification (keep `find_by_key`, `resolve_entity` seed branch)
- No settlement / metering changes

---

## Deliverables

- `prompts/cursor/done/2026-06-10-1000-entity-uuid4-unification-slice13/output.md`
- `prompts/cursor/done/2026-06-10-1000-entity-uuid4-unification-slice13/review.md`

**For Grok + Paul** section in `output.md`:

- Mark Slice 13 done in `TODO.md` under seed-elimination track
- Note behavior change: seed hits now mirror into `entities.json`
- Queue Slice 14 (remove runtime seed) if approved

---

## Verify

```bash
uv run ruff check src tests
uv run pytest -m smoke -q
rg uuid5 src/   # expect no matches
```
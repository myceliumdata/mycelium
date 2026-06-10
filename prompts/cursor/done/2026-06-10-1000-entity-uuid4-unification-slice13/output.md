# Slice 13 — Entity ID unification (uuid4 everywhere)

## Summary

Unified entity ID allocation on **uuid4** with **`entities.json` `bind_index` as persistence**. Removed seed `uuid5`. Runtime seed resolution (`find_by_key`, `resolve_entity` seed branch) unchanged — Slice 14.

## Changes

| Area | Change |
|------|--------|
| `entity_registry.py` | `ensure_bound_entity(name, employer, *, source, validation_state)` — uuid4 on miss, bind_index reuse on hit; `bind_provisional` delegates |
| `seed.py` | `_enrich_person` mirrors each row via `ensure_bound_entity(..., source="seed_bootstrap")`; uuid5 removed |
| `storage/core.py` | `seed_from_file` uses `ensure_bound_entity` for rows without explicit `id` |
| `runtime.py` | `refresh_runtime_from_disk` calls `reset_entity_registry()` before seed reload |
| Tests | Seed-mirror assertions; MCP reload stability test; entity lookups by `id` not `next(iter)` |
| Docs | `architecture.md`, `full-code-walkthrough.md`, program slice map → **Shipped** |

## Behavior change

Seed hits now **write mirror rows** into `entities.json` (`source: seed_bootstrap`, `validation_state: validated`). First `find_by_key` / seed load enriches all seed people into the registry. Tests that assumed `len(entities) == 1` or “no registry write on seed hit” were updated.

## Tests

**32 passed** — entity bind/growth/validation/unknown_mvr  
**266 passed** — full smoke (`-m smoke`)

```bash
uv run ruff check src tests
uv run pytest tests/test_entity_registry_bind.py tests/test_entity_growth.py \
  tests/test_entity_validation.py tests/test_entity_unknown_mvr.py -q
uv run pytest -m smoke -q
rg uuid5 src/   # clean
```

## For Grok + Paul

- Mark **Slice 13** done in `TODO.md` under seed-elimination track
- Note behavior change: seed hits mirror into `entities.json`; MCP reload reuses ids via `bind_index`
- Queue **Slice 14** (remove runtime seed resolution) if approved
- Review folder: `prompts/cursor/done/2026-06-10-1000-entity-uuid4-unification-slice13/`
- Suggested commit message (after review):

```
Unify entity IDs on uuid4 with entities.json persistence (Slice 13).

ensure_bound_entity for seed and bind; remove uuid5; MCP registry reset;
update tests/docs for seed registry mirror.
```

- **Did not edit `TODO.md`** (per governance)

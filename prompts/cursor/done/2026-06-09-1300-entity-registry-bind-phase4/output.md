# Output — Entity registry + provisional bind (Phase 4, slice `1300`)

## Summary

Introduced runtime **`entities.json`**, **`EntityQuery.binding`**, unified **`resolve_entity`**, and provisional bind with **`entity_bound_provisional`** / **`entity_under_specified`**. Duplicate bind returns **`found`** (Q4e). No validation loop, no email research on provisional entities.

## Changes

| File | Change |
|------|--------|
| `src/agents/entity_registry.py` | **New** — `EntityRegistry`, atomic save, `bind_index`, `bind_provisional()` |
| `src/agents/entity_resolution.py` | **`resolve_entity(query)`** — registry → seed → suggest → unknown/under_specified/bind |
| `src/agents/supervisor.py` | Short-circuits for bind/under_specified; skips specialists on provisional registry |
| `src/agents/dispatch.py` | Assemble paths for bind, under_specified, duplicate bind, provisional re-query |
| `src/agents/responses.py` | `response_entity_bound_provisional`, `response_entity_under_specified`, `response_registry_provisional_identity`; `response_found(message=…)` |
| `src/models/state.py` | `EntityQuery.binding`; graph flags `registry_provisional_only`, `duplicate_bind` |
| `src/network/paths.py` | `entities_path`, `MYCELIUM_ENTITIES_PATH` in `runtime_path()` map |
| `src/network/mvr.py` | `normalize_binding()`, `required_bind_fields()` |
| `src/network/introspection.py` | `policy.entity_bind` |
| `src/mycelium_mcp/server.py` | Schema/doc hints for binding |
| `.gitignore` | `examples/networks/**/entities.json` |
| `tests/test_entity_registry_bind.py` | **New** — 10 smoke tests (spec matrix) |
| `tests/conftest.py` | `reset_entity_registry` in session cleanup |
| Entity protocol fixtures | `MYCELIUM_ENTITIES_PATH` + registry reset |

## Resolution order

1. Registry `bind_index` (name + `binding.employer`)
2. Registry by uuid `entity_key`
3. Seed `find_by_key`
4. Near-miss suggest (slice 1)
5. `entity_unknown` / `entity_under_specified` / provisional bind

## Locked behaviors

| Case | Outcome |
|------|---------|
| Murphy + `binding.employer` (first) | `entity_bound_provisional`, row in `entities.json` |
| Repeat same bind | `found`, same id, “already bound” message |
| Murphy @ Acme + Murphy @ Beta | two uuid4 rows |
| Bound Murphy + `email` | bind/provisional identity only — no specialists |
| Seed Aaron Holiday + `email` | normal `assembled` — no registry write |
| Partial binding (`employer: ""`) | `entity_under_specified` |

## Tests

```bash
uv run pytest tests/test_entity_registry_bind.py -m smoke -q   # 10 passed
uv run pytest -m smoke -q                                     # 194 passed
```

## For Grok + Paul

- Mark **Slice 4 (`1300`)** done in `TODO.md` when reviewed.
- **Slice 5 (`1400` validation)** and **Slice 6 (research gate)** remain queued.
- Admin UI registry display still deferred per `admin-ui-backlog.md`.

## Exit criteria

- [x] `entities.json` + `MYCELIUM_ENTITIES_PATH`
- [x] `EntityQuery.binding` with unknown keys ignored
- [x] Provisional bind + idempotent duplicate → `found`
- [x] No specialist/Tavily on bind turn or provisional re-query with attrs
- [x] Smoke matrix green

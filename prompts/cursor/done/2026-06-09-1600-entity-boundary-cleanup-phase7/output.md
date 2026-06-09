# Output — Seed vs specialists boundary cleanup (Phase 7, slice `1600`)

## Summary

Registry/supervisor owns bind fields (`name`, `employer`). Specialists receive `entity_id`, read-only `bind`, and extended-attrs-only `storage` snapshots via `build_context`. Legacy `name`/`employer` in specialist `storage.json` are ignored on read; new writes never include them. **`core_identity.py` deleted**; no runtime imports remain.

## Changes

| File | Change |
|------|--------|
| `src/agents/context.py` | `entity_id` + `bind` + stripped `specialists` storage; `bind_from_record`, `strip_bind_fields` |
| `src/agents/dispatch.py` | `build_context_node` emits new context shape (no top-level `seed`) |
| `src/agents/factory/templates/specialist_agent.py.j2` | `entity_id`/`bind` identity; `_research_context()` for research prompts |
| `src/agents/factory/templates/research/*.j2` | Research prompts reference `context.bind` |
| `src/agents/specialists/base.py` | `storage_strategy.json` documents bind vs extended boundary |
| `src/agents/routing.py` | Uses `agents.seed.find_by_key`; injectable `seed_lookup` for tests |
| `src/agents/core_identity.py` | **Deleted** |
| `examples/networks/crm/specialists/contact_specialist.py` | Regenerated from template |
| `tests/test_entity_boundary.py` | **New** — factory storage, build_context, research bind, no `core_identity` |
| `tests/*` | Removed `reset_core_identity`; context fixtures use `entity_id`/`bind` |
| `docs/architecture.md` | Dropped `core_identity` from legacy list |

## Specialist context shape (post–build_context)

```python
{
  "entity_id": "<uuid>",
  "bind": {"name": "…", "employer": "…"},
  "specialists": {"contact": { "<uuid>": { "email": … } }},
  "_meta": { … },
}
```

## Tests

```bash
uv run pytest tests/test_entity_boundary.py -m smoke -q   # 3 passed
uv run pytest -m smoke -q                                 # 208 passed
```

## For Grok + Paul

- Mark **Slice 7 (`1600`)** done in `TODO.md` when reviewed.
- Admin backlog item #8 (registry vs specialist fields in drill-down) already listed in `admin-ui-backlog.md`.
- Slice 8 (`1700`) entity growth is next in queue.

## Exit criteria

- [x] Factory-created storage lacks `name`/`employer` on new writes
- [x] Research uses `bind` from context (not storage copy)
- [x] No runtime `core_identity` imports
- [x] Reference `contact_specialist` regenerated
- [x] Smoke green (208)

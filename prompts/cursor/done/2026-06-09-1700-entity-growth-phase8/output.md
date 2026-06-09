# Output — Seed from queries & network growth (Phase 8, slice `1700`)

## Summary

Hardened the network growth path with registry **data attribution**: after successful specialist research on registry-grown entities, `entities.json` rows gain `attr_sources` and `last_researched_at` for attrs written in that pass. Full Paul Murphy smoke arc (unknown → bind → validate → email → re-query). Growth model documented for operators.

**Deferred per spec:** empty-seed fixtures, seed export, seed/grown linking (Q8b–Q8d).

## Changes

| File | Change |
|------|--------|
| `src/agents/entity_registry.py` | `attr_sources`, `last_researched_at` on `RegistryEntity`; `record_research_attribution()` |
| `src/agents/entity_growth.py` | **New** — parse research audit, apply attribution after invoke |
| `src/agents/dispatch.py` | `invoke_specialists_node` stores per-contrib audit; calls growth attribution |
| `src/network/introspection.py` | `policy.entity_growth` |
| `examples/networks/crm/README.md` | Network growth from queries section |
| `tests/test_entity_growth.py` | **New** — Paul Murphy arc, seed unchanged, parse helper |

## Growth flow

```
bind → validate → gated research → specialist storage (entity_id)
  → registry attr_sources + last_researched_at (attrs updated this pass)
```

## Tests

```bash
uv run pytest tests/test_entity_growth.py -m smoke -q   # 2 passed
uv run pytest -m smoke -q                                 # 212 passed
```

## For Grok + Paul

- Mark **Slice 8 (`1700`)** done in `TODO.md` when reviewed.
- Slice 9 (`1800`) entity protocol polish is next in queue.
- Admin UI for `attr_sources` / `last_researched_at` remains backlog #9.

## Exit criteria

- [x] Registry `attr_sources` + `last_researched_at` after successful research
- [x] Paul Murphy full arc smoke test
- [x] Seed person unchanged after registry growth on other entities
- [x] Growth model documented
- [x] Smoke green (212)

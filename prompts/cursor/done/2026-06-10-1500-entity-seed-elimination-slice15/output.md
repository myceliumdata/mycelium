# Slice 15 — Seed elimination: registry-only resolution

## Summary

Query-time entity resolution now uses **`entities.json` only**. Removed seed branches from `resolve_entity` / `resolve_entity_for_lookup`; suggestions scan registry rows. Added `lookup_entities_by_key` for callers and test fixtures.

## Changes

| File | Change |
|------|--------|
| `src/agents/entity_resolution.py` | Registry-only resolution; `lookup_entities_by_key`; suggestions from registry; skip suggestions when binding includes employer; `multiple` for ambiguous `seed_bootstrap` names |
| `src/agents/routing.py` | `lookup_entities_by_key` default (legacy `seed_lookup` param retained for tests) |
| `src/agents/dispatch.py` | Docstrings / audit messages: entity not seed |
| `src/network/introspection.py` | `_seed_people_count` reads `seed.json` on disk (no `get_seed_data`) |
| `tests/network_helpers.py` | `import_seed_for_test`, `import_seed_at_root` |
| `tests/test_entity_*.py` | Fixtures use `import_seed_for_test` instead of `get_seed_data` / `seed_from_file` |
| `tests/test_network_status.py` | Registry lookup + bootstrap import in status tests |

### Out-of-scope touch (required for tests)

| File | Why |
|------|-----|
| `src/agents/research_gate.py` | Multiple validated registry matches (e.g. two Kevin Zhang rows) were incorrectly gated after all matches gained `_registry: True`. Minimal fix: allow research when all matches are validated. Full simplification deferred to Slice 16. |

`agents/seed.py`, `context.py`, `runtime.py`, and admin UI unchanged (Slices 16–17).

## Tests

**42 passed** — slice 15 verify set  
**43 passed** — broader entity smoke

```bash
uv run ruff check src/agents/entity_resolution.py src/agents/routing.py src/agents/dispatch.py
uv run pytest tests/test_entity_key_suggestions.py tests/test_entity_unknown_mvr.py \
  tests/test_entity_registry_bind.py tests/test_network_status.py -m smoke -q
```

## For Grok + Paul

- Mark **Slice 15** done in `TODO.md` under seed-elimination track
- **Slice 16** next: context + runtime seed removal; complete `research_gate` simplification
- Note: `research_gate.py` minimally updated — include in review scope even though prompt file list omitted it
- Review folder: `prompts/cursor/done/2026-06-10-1500-entity-seed-elimination-slice15/` (`prompt.md` + `output.md` only — no `review.md` per governance)
- Suggested commit message (after review):

```
Registry-only entity resolution (Slice 15).

lookup_entities_by_key; registry suggestions; test fixtures import seed;
research_gate fix for multiple validated registry rows.
```

- **Did not edit `TODO.md`** (per governance)

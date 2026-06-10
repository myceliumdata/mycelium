# Slice 17 — Seed elimination: delete runtime seed module

## Summary

Deleted `agents/seed.py` and the legacy `mycelium seed` CLI. All tests now bootstrap CRM identity via `import_seed_for_test` / `import_seed_at_root` and `reset_entity_registry` for cleanup.

## Changes

| File | Change |
|------|--------|
| `src/agents/seed.py` | **Deleted** |
| `src/main.py` | Removed `seed` subcommand (parser + handler) |
| `src/storage/core.py` | Docstring: identity via `entities.json` / `import_seed_file` |
| `tests/network_helpers.py` | Enhanced `import_seed_for_test` (optional copy + env); kept `import_seed_at_root` |
| `tests/conftest.py` | Session cleanup uses `reset_entity_registry` only |
| `tests/test_network_integration.py` | `_reset_runtime_singletons` drops seed reset |
| `tests/test_*.py` (20+ files) | Replaced `agents.seed` imports with registry helpers + `import_seed_for_test` |
| `tests/test_network_polish.py` | `test_missing_seed_import_returns_zero` (was seed-loader FileNotFoundError) |
| `tests/test_entity_rename.py` | MCP round-trip imports seed into `entities.json` |

## Verification

```bash
# no matches in src/ or tests/
rg 'agents\.seed|get_seed_data|reset_seed_data' src/ tests/

uv run ruff check src tests   # All checks passed
uv run pytest -m smoke -q     # 271 passed, 26 deselected
```

No smoke failures. Slice 16 carry-over (`test_mcp_query_entity_round_trip_json`) is fixed.

## For Grok + Paul

- Mark **Slice 17** done in `TODO.md` under seed-elimination track
- **Slice 18** next: admin UI, README, architecture/docs stale references (`agents.seed`, `find_by_key` still appear in `docs/architecture.md`, `docs/full-code-walkthrough.md`, etc.)
- Consider batch commit for seed-elimination slices 14–17 when ready
- Review folder: `prompts/cursor/done/2026-06-10-1700-entity-seed-elimination-slice17/`
- Suggested commit message (after review):

```
Delete runtime seed module and legacy seed CLI (Slice 17).

Remove agents.seed; tests bootstrap via import_seed_for_test;
mycelium seed subcommand removed; smoke 271 green.
```

- **Did not edit `TODO.md`** (per governance)

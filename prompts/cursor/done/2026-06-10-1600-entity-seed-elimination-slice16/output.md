# Slice 16 — Seed elimination: context + runtime

## Summary

Removed seed from context assembly, MCP/admin runtime refresh, and research gate. Matched rows are always registry rows; bind fields resolve from `entities.json` by id.

## Changes

| File | Change |
|------|--------|
| `src/agents/context.py` | `_resolve_identity_rows` loads from entity registry by id; removed `get_seed_data` |
| `src/agents/runtime.py` | `refresh_runtime_from_disk` drops `reset_seed_data()` / `get_seed_data()` |
| `src/agents/research_gate.py` | Gating on `_validation_state == "validated"` only |
| `src/mycelium_admin/server.py` | `_refresh_read_cache` → `reset_entity_registry()` |
| `src/agents/supervisor.py` | Audit log always `resolved via registry` |
| `tests/test_mcp_runtime_reload.py` | Stable ids via persisted `entities.json` + `lookup_entities_by_key` |
| `tests/test_admin_daemon.py` | Registry reset on status; entities hot-reload test; import on client setup |
| `tests/test_entity_boundary.py` | New test: `build_full_context` resolves bind from registry |
| `tests/test_entity_research_gate.py` | Gate assert uses validated registry match |

## Tests

**43 passed** — slice 16 verify set (+ boundary + admin)

```bash
uv run pytest tests/test_mcp_runtime_reload.py tests/test_entity_research_gate.py tests/test_supervisor_routing.py -m smoke -q
```

**270 passed, 1 failed** — full smoke (`test_entity_rename.py::test_mcp_query_entity_round_trip_json` — copies `seed.json` without `import_seed_for_test`; fix in Slice 17 test sweep)

## For Grok + Paul

- Mark **Slice 16** done in `TODO.md` under seed-elimination track
- **Slice 17** next: delete `agents/seed.py`, sweep remaining test seed imports (`test_entity_rename.py`, etc.)
- Commit seed-elimination slices 14–16 + fixes when ready
- Review folder: `prompts/cursor/done/2026-06-10-1600-entity-seed-elimination-slice16/`
- Suggested commit message (after review):

```
Remove seed from context and runtime refresh (Slice 16).

Context resolves bind from registry; MCP/admin reset entities only;
research gate uses validation_state; supervisor audit registry-only.
```

- **Did not edit `TODO.md`** (per governance)

# mcp-runtime-reload (slice 1200) — Output

## Claim

Moved `prompts/cursor/next/2026-06-05-1200-mcp-runtime-reload.md` → `prompts/cursor/in-progress/2026-06-09-1200-mcp-runtime-reload/prompt.md`.

## Approach

Added `src/agents/runtime.py` with `refresh_runtime_from_disk()` for long-lived MCP parity with per-invocation CLI processes:

1. `load_dotenv(override=True)` — pick up `.env` changes
2. `reset_agent_registry()` + `get_agent_registry()` — reload `data/agent_registry.json`
3. `reset_category_tree()` + `get_category_tree()` — reload `data/categories.json`
4. `reset_seed_data()` + `get_seed_data()` — reload seed JSON
5. `reset_agent_factory()` — fresh factory binding
6. `evict_cached_specialist_modules()` — drop `dyn_specialist_*` and `agents.specialists.*_specialist` from `sys.modules` (not `base`)

Called at the start of `_run_mcp_query` (covers `query_person` and `health_check` ping) and `list_specialist_routing`, after `_bootstrap()`.

**Intentionally not reset:** `reset_core_graph()` on happy path — MCP keeps sync checkpointer / `thread_id` continuity. Graph reset remains on query error recovery only.

## Files changed

| File | Change |
|------|--------|
| `src/agents/runtime.py` | New refresh + eviction helpers |
| `src/mycelium_mcp/server.py` | Wire refresh; update MCP instructions |
| `tests/test_mcp_runtime_reload.py` | Smoke tests |
| `README.md` | Shorten MCP restart guidance |

## Verification

```
$ uv run pytest -m smoke -q
52 passed, 11 deselected in 2.73s

$ uv run ruff check src tests
All checks passed!
```

## Manual MCP / CLI parity (documented)

1. Start MCP: `uv run mycelium-mcp` (leave running).
2. Other terminal: `uv run mycelium query --person-key "Andrea Kalmans" --attributes email` (with keys set, populates registry + contact storage).
3. Without restarting MCP, call `query_person` with the same `person_key` and `requested_attributes: ["email"]` (MCP client or `from mycelium_mcp.server import _run_mcp_query`).
4. **Expected:** MCP `results` include `email` when CLI did (same disk registry/storage; refresh runs before each MCP query).

If parity fails after deploy, restart MCP once; routine registry/`.env`/storage changes should not require restart.

## Tradeoffs

- Per-query refresh adds small overhead (registry/seed JSON parse + module eviction) vs stale state bugs.
- Core SQLite / graph checkpoint not reloaded each query — specialist JSON storage is read fresh via re-imported modules and `SpecialistStorage.load()`.
- `refresh_runtime_from_disk(reload_dotenv=False)` available for tests to avoid clobbering monkeypatched env.

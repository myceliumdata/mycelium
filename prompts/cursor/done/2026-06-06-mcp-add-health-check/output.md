# Task output — MCP health_check tool

## Claim

Moved `prompts/cursor/next/2026-06-06-mcp-add-health-check.md` → `prompts/cursor/in-progress/2026-06-06-mcp-add-health-check/prompt.md` before implementation.

## Summary

Added `health_check()` MCP tool in `src/mycelium_mcp/server.py` only. External agents can cheaply verify the server is alive and that storage, graph, lightweight tools, and the stabilized query path (sync checkpointer + recovery wrapper) work.

**Tool name:** `health_check` (clearer than `health` for MCP tool discovery).

**No new Pydantic models** — returns a plain JSON string like `list_specialist_routing`.

**Checks (each isolated in try/except):**
| Check | What it does |
|-------|----------------|
| `storage` | `get_storage()` after `_bootstrap()` |
| `graph` | `get_core_graph()` |
| `lightweight_tool` | `list_specialist_routing()` parses with expected `message` |
| `ping_query` | `_run_mcp_query` with seed key `Nichanan Kesonpat` |

**Status:** `ok` if all checks are `"ok"`; otherwise `degraded`. Outer try/except always returns parseable JSON.

**info block:** Reports `checkpointer: sync (forced for MCP)`, `recovery_wrapper: active`, `server: mycelium-mcp`.

**FastMCP instructions** updated to mention `health_check()` for diagnostics.

Existing `query_person`, `list_specialist_routing`, resources, `_bootstrap`, `_run_mcp_query` recovery, and `MYCELIUM_USE_SYNC_CHECKPOINTER` forcing unchanged.

## Verification

### `uv run ruff check src/mycelium_mcp/server.py`

```
All checks passed!
```

### `uv run pytest -m smoke -q`

```
13 passed, 9 deselected in 0.05s
```

### Manual smoke

```
{
  "status": "ok",
  "checks": {
    "storage": "ok",
    "graph": "ok",
    "lightweight_tool": "ok",
    "ping_query": "ok"
  },
  "info": {
    "checkpointer": "sync (forced for MCP)",
    "recovery_wrapper": "active",
    "server": "mycelium-mcp"
  },
  "message": "Mycelium MCP server is responsive."
}
health_check smoke: ok
list_specialist_routing: ok
query_person: ok
```

## Follow-ups (optional)

- Document `health_check` in README / architecture MCP section (separate prompt; out of scope here).
- Consider whether Claude Desktop should call `health_check` on first connect (product decision).
- TODO.md observability bullet could mention MCP health tool (minimal note via separate doc prompt if desired).

## Open questions

- Add a `mycelium://schema/health` resource later?
- Should degraded `ping_query` include more detail in `checks` without exposing internals to untrusted clients?

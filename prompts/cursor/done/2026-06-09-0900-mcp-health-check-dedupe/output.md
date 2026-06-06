# mcp-health-check-dedupe (slice 0900) — Output

## Claim

Moved `prompts/cursor/next/2026-06-06-0900-mcp-health-check-dedupe.md` → `prompts/cursor/in-progress/2026-06-09-0900-mcp-health-check-dedupe/prompt.md`.

**Depends on:** `prompts/cursor/done/2026-06-09-1200-mcp-runtime-reload/`.

## Approach

Split MCP server into refresh-wrapped public entry points and internal helpers without refresh:

| Helper | Role |
|--------|------|
| `_routing_payload()` | Registry list dict (no bootstrap/refresh) |
| `_execute_mcp_query()` | Parse + `run_query` + serialize / error recovery (no bootstrap/refresh) |
| `_run_mcp_query()` | `_bootstrap()` → `refresh_runtime_from_disk()` → `_execute_mcp_query()` |
| `list_specialist_routing()` | bootstrap + refresh + serialize `_routing_payload()` |
| `health_check()` | bootstrap + **one** refresh; sub-checks call `_routing_payload()` and `_execute_mcp_query()` directly |

`query_person` unchanged (still uses `_run_mcp_query`).

## Files changed

- `src/mycelium_mcp/server.py`
- `tests/test_mcp_runtime_reload.py` — `test_health_check_refreshes_runtime_once`, `test_list_specialist_routing_refreshes_runtime_once`

## Verification

```
$ uv run pytest -m smoke -q tests/test_mcp_runtime_reload.py
4 passed

$ uv run ruff check src/mycelium_mcp/server.py tests/test_mcp_runtime_reload.py
All checks passed!
```

### Manual smoke

```
health_check: ok {'storage': 'ok', 'graph': 'ok', 'lightweight_tool': 'ok', 'ping_query': 'ok'}
```

## Tradeoffs

- `health_check` now refreshes once up front (before storage/graph checks) instead of twice via nested tools — sub-checks see post-refresh state consistently.
- No global skip flags; explicit helper split keeps behavior testable.

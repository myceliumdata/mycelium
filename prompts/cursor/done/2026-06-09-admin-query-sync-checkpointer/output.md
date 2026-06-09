# Output — Admin `POST /query` sync checkpointer fix

## Summary

Fixed `500 Internal Server Error` on admin `POST /query` caused by `AsyncSqliteSaver` lock affinity across per-request `asyncio.run()` loops. Admin now matches MCP/CLI: force sync checkpointer before importing `graphs.core`.

## Changes


| File                           | Change                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `src/mycelium_admin/server.py` | Set `MYCELIUM_USE_SYNC_CHECKPOINTER=1` before `from graphs.core import run_query`                                  |
| `bin/restart-admin`            | Export env when spawning daemon (belt-and-suspenders)                                                              |
| `tests/test_admin_daemon.py`   | `test_admin_module_forces_sync_checkpointer` — reset + compile graph, assert sync saver; docstrings on query tests |


## Tests

```bash
uv run pytest tests/test_admin_daemon.py -m smoke -q   # 12 passed
uv run ruff check src/mycelium_admin/server.py tests/test_admin_daemon.py
```

## For Grok + Paul

- **Restart required:** After deploy, run `./bin/restart-admin` (or restart `mycelium-admin`) so the process re-imports `server.py` and compiles the graph with sync `SqliteSaver`. An already-running daemon may still hold the async singleton from before the fix.
- Manual: Run query panel — Paul Murphy + employer binding should return JSON (not 500).
- No `TODO.md` edits by Cursor.

## Exit criteria

- Admin server sets sync checkpointer env before graph import
- Smoke tests cover sync compilation + `POST /query` paths
- `restart-admin` exports env for spawned process


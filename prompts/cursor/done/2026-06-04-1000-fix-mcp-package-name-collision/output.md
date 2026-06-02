# Output: Fix MCP package name collision

## Summary

Renamed `src/mcp/` → `src/mycelium_mcp/` so the `mycelium-mcp` entry point and `from mycelium_mcp.server import ...` resolve to this project’s FastMCP server instead of the official `mcp` SDK (a `fastmcp` dependency).

## Problem

`setuptools` installed our server as top-level package `mcp`, colliding with the PyPI `mcp` package. That caused:

```text
ImportError: cannot import name 'run_server' from 'mcp.server'
```

The 0950 server logic was correct but unreachable via `uv run mycelium-mcp`.

## Changes

| File | Change |
|------|--------|
| `src/mcp/` → `src/mycelium_mcp/` | Directory rename (`server.py`, `__init__.py`) |
| `pyproject.toml` | `mycelium-mcp = "mycelium_mcp.server:run_server"` |
| `README.md` | Mermaid label, package table path, repo layout tree |
| `src/mycelium_mcp/__init__.py` | Docstring noting rename |
| `src/mycelium_mcp/server.py` | Module docstring only (no behavior change) |

Console script name remains `mycelium-mcp`. No changes under `prompts/cursor/done/`.

## Verification

```bash
uv sync
uv run ruff check src tests    # clean
uv run pytest -q               # 19 passed
uv run mycelium-mcp            # FastMCP banner + "Starting MCP server 'Mycelium'" (no ImportError)
uv run python -c "from mycelium_mcp.server import query_person, submit_person_data, run_server, _parse_query_payload; ..."
# Import successful; thread_id parse spot-check OK
```

**Note:** `uv run mycelium-mcp --help` starts the stdio MCP server (FastMCP UX), not a traditional `--help` page. Success criterion is no import collision and the server starting.

After pulling this change, run `uv sync` (or recreate the venv) so the entry point is rebuilt.

## Open questions

None.

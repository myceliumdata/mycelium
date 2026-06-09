# Admin `POST /query` — force sync checkpointer (event-loop fix)

## Objective

Fix `500 Internal Server Error` on `POST /query` from the admin daemon when running graph queries (e.g. Paul Murphy + Ormi Labs bind).

## Root cause

`mycelium-admin` is a long-lived HTTP process that calls `run_query()` from a FastAPI worker thread. It imports `graphs.core` **without** setting `MYCELIUM_USE_SYNC_CHECKPOINTER=1`, so the graph uses `AsyncSqliteSaver`. Each `run_query` calls `asyncio.run()` in a **new** event loop while the checkpointer lock was created on a **different** loop →:

```
RuntimeError: ... Lock ... is bound to a different event loop
```

MCP (`src/mycelium_mcp/server.py`) and CLI (`src/main.py`) already set `MYCELIUM_USE_SYNC_CHECKPOINTER=1` **before** importing `graphs.core` for exactly this reason.

## Constraints

- Match the MCP pattern: set env var at module top, before `from graphs.core import ...`.
- Do not change graph logic unless required for admin-only edge cases.
- Add a smoke test that reproduces admin query path with sync checkpointer asserted or query succeeding after fix.
- May modify: `src/mycelium_admin/server.py`, `tests/test_admin_daemon.py`, optionally `bin/restart-admin` (export env when spawning daemon — belt-and-suspenders only if server.py fix is insufficient).

## Implementation

1. In `src/mycelium_admin/server.py`, immediately after `import os` and before any `graphs.core` import:

   ```python
   os.environ["MYCELIUM_USE_SYNC_CHECKPOINTER"] = "1"
   ```

2. Ensure `graphs.core` is not imported earlier in the admin entry path before this runs (verify `mycelium-admin` console script imports `server` as root).

3. Extend `tests/test_admin_daemon.py` — `test_admin_query_seed_entity` should pass on CI; add a test comment noting sync checkpointer requirement for long-lived admin process.

4. Optional: document in `output.md` that Paul must **restart** `mycelium-admin` after deploy (graph singleton may already be compiled with async saver if process started before fix).

## Verification

```bash
uv run pytest tests/test_admin_daemon.py -m smoke -q
uv run ruff check src tests bin/
```

Manual: `./bin/restart-admin`, Run query panel — Paul Murphy + Ormi Labs employer binding should return JSON (not 500).

## For Grok + Paul

- No `TODO.md` edits by Cursor.
- After merge: Paul restarts admin daemon before retesting.
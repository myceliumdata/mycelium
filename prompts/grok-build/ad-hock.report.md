# Handoff Report: LangGraph Async / Blocking-Call Fix (Mycelium)

**Date:** 2026-06-04  
**Context:** Paul ran `langgraph dev` and received LangGraph’s warning about synchronous blocking calls degrading ASGI performance.  
**Scope:** Refactor graph execution and I/O paths for `langgraph dev` compatibility while keeping CLI/MCP behavior unchanged.  
**Status:** Implemented locally; **19/19 tests passing**, ruff clean. **Not committed** unless Paul requests.

---

## Problem Summary

`langgraph.json` exposes the graph via:

```json
"mycelium": "./src/graphs/core.py:get_core_graph"
```

LangGraph Studio/dev runs this graph in an **ASGI** server using **`ainvoke`**. The codebase had several **sync** patterns that block the event loop:

1. **`graph.invoke()`** in `src/graphs/core.py` (sync graph execution)
2. **`sqlite3.connect` + `SqliteSaver`** for LangGraph checkpoints (sync DB I/O on every step)
3. **Sync graph nodes** (`def supervisor_agent`, etc.) while dev expects async nodes
4. **Sync SQLite CRM storage** in `src/storage/core.py`, reached from the supervisor via `evaluate_supervisor_turn` → `CoreIdentity.find_by_key` / `persist`

There are **no HTTP calls** (`requests`, `httpx`, etc.) in the current codebase. Blocking was entirely **SQLite + sync invoke/nodes**.

A related pre-existing issue (already fixed in a prior task): MCP package name collision (`mcp` vs official SDK) was resolved by renaming to `mycelium_mcp` — separate from this async work.

---

## Root Cause (by file)

| File | Blocking behavior |
|------|-------------------|
| `src/graphs/core.py` | `graph.invoke()`, `SqliteSaver` + `sqlite3.connect` for checkpoints |
| `src/agents/supervisor.py` | Sync node calling routing that hits `CoreStorage` (sync `sqlite3`) |
| `src/agents/enrich.py`, `validator.py` | Sync `def` nodes (no I/O, but incompatible with async graph runner expectations) |
| `src/storage/core.py` | Sync `sqlite3` for CRM `people` table (unchanged; accessed from supervisor path) |

---

## Solution Approach

**Principle:** Use native async where LangGraph provides it; use `asyncio.to_thread()` where a full async rewrite isn’t justified yet.

### 1. Async checkpointer (`src/graphs/core.py`)

- **Removed:** `sqlite3` + `langgraph.checkpoint.sqlite.SqliteSaver`
- **Added:** `aiosqlite` + `langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver`
- New helper `_setup_async_checkpointer()` runs `await aiosqlite.connect()`, `await saver.setup()`
- `build_core_graph()` still sync API; uses `asyncio.run(_setup_async_checkpointer(...))` once at compile time
- `_close_async_checkpointer()` added for test teardown in `reset_core_graph()`

### 2. Async graph invocation (`src/graphs/core.py`)

- **New:** `async def _ainvoke_core_graph(...)` using `await graph.ainvoke(...)`
- LangSmith `@traceable` wrapper updated to **async** `_traced_ainvoke` (still captures `trace_id` after invoke)
- **Sync bridge:** `_invoke_core_graph()` → `asyncio.run(_ainvoke_core_graph(...))` for CLI/MCP `run_query()`

Public API unchanged: `run_query()` remains synchronous for `main.py` and `mycelium_mcp/server.py`.

### 3. Async supervisor + threaded storage (`src/agents/supervisor.py`)

- `supervisor_agent` → `async def supervisor_agent`
- `evaluate_supervisor_turn(...)` wrapped in `await asyncio.to_thread(...)` so sync CRM SQLite does not block the event loop

### 4. Async enrich/validator nodes

- `enrich_agent`, `validator_agent` → `async def` (in-memory only; no `to_thread` needed)

### 5. Dependency

- Added explicit `aiosqlite>=0.20.0` to `pyproject.toml` (also transitive via `langgraph-checkpoint-sqlite`)

---

## Files Modified

| File | Change |
|------|--------|
| `src/graphs/core.py` | Async checkpointer, `ainvoke`, `asyncio.run` bridge, checkpointer cleanup |
| `src/agents/supervisor.py` | Async node + `asyncio.to_thread` for routing/storage |
| `src/agents/enrich.py` | `async def enrich_agent` |
| `src/agents/validator.py` | `async def validator_agent` |
| `pyproject.toml` | `aiosqlite` dependency |

**Not modified:** `src/storage/core.py` (still sync sqlite3), `langgraph.json`, `docs/architecture.md`, MCP/CLI entry points (behavior preserved via sync bridge).

---

## Verification Performed

```bash
uv sync
uv run pytest -q          # 19 passed
uv run ruff check src tests  # clean
```

Existing tests cover:

- Core graph lookup/ingest paths (`tests/test_core_graph.py`)
- `thread_id` / `trace_id` on `PersonResponse` (`tests/test_core_graph.py`, `tests/test_trace_capture.py`)
- LangSmith trace capture with patched tracing (`test_run_query_sets_trace_id_on_response_when_captured`)

**Recommended manual check for Grok/Paul:**

```bash
langgraph dev
```

Confirm the synchronous-blocking warning no longer appears (or is materially reduced).

---

## Behavioral Guarantees

| Consumer | Behavior |
|----------|----------|
| `langgraph dev` / Studio | Uses compiled graph with **async nodes** + **AsyncSqliteSaver**; dev server can `ainvoke` without blocking |
| CLI (`uv run mycelium query/ingest`) | Still calls `run_query()` → sync `_invoke_core_graph` → `asyncio.run(ainvoke)` |
| MCP (`uv run mycelium-mcp`) | Same as CLI |
| Tests | Unchanged call pattern; all pass |

No changes to `PersonResponse` shape, routing logic, or MCP `thread_id` / `trace_id` wiring.

---

## Intentional Non-Goals / Deferred Work

- **Full async CRM storage** (`CoreStorage` → `aiosqlite`): deferred; supervisor uses `to_thread` instead
- **Async `run_query()`** public API: not added; sync bridge sufficient for now
- **Startup seed I/O** in `get_storage().seed_from_file()`: still sync; runs outside graph hot path (could warn if called from async context during bootstrap)
- **Documentation updates** for async architecture: not done in this pass
- **Git commit**: pending Paul’s instruction

---

## Risks / Gotchas for Review

1. **`asyncio.run()` in `build_core_graph()`** — fine for current sync test/CLI startup; would fail if `build_core_graph()` were ever called *inside* an already-running event loop (not the case today).
2. **`_close_async_checkpointer()`** — if called while a loop is running, uses `asyncio.create_task` (fire-and-forget); test teardown uses `asyncio.run` and is safe.
3. **Thread pool overhead** — supervisor CRM access goes through `to_thread`; acceptable for Phase 1 volume; revisit if latency becomes an issue.

---

## Suggested Follow-Ups for Grok Build

1. Confirm `langgraph dev` warning is resolved in Paul’s environment.
2. Decide whether to document async graph contract in `docs/architecture.md`.
3. Optional: add `run_query_async()` for native async callers.
4. Optional: migrate `CoreStorage` to `aiosqlite` and drop `to_thread` in supervisor.
5. Commit strategy: single commit e.g. *“Make LangGraph core path async for langgraph dev (AsyncSqliteSaver, ainvoke, async nodes)”*.

---

## Queue / Prior Task Context (same session, earlier)

Paul also completed Cursor queue task **`2026-06-04-1000-fix-mcp-package-name-collision`** (`src/mcp/` → `src/mycelium_mcp/`, commit `a2f1660`). That unblocks `uv run mycelium-mcp`; separate from but complementary to this async fix for end-to-end MCP + Studio workflows.

---

*Prepared by Cursor for Grok Build review.*

# Task: MCP `health_check` — dedupe runtime refresh

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md` (MCP public interface)
- `src/mycelium_mcp/server.py` (`health_check`, `list_specialist_routing`, `_run_mcp_query`)
- `src/agents/runtime.py` (`refresh_runtime_from_disk`)
- `tests/test_mcp_runtime_reload.py` (existing refresh smoke tests)
- `prompts/cursor/done/2026-06-09-1200-mcp-runtime-reload/` (prior slice context)

**Depends on:** MCP runtime reload landed (`7e991cb`); `TODO.md` near-term item **MCP `health_check` double refresh**.

---

## Problem (why this slice exists)

`health_check()` currently triggers **`refresh_runtime_from_disk()` twice** in one invocation:

1. **`list_specialist_routing()`** — calls `_bootstrap()` then `refresh_runtime_from_disk()` (lines ~129–130).
2. **`_run_mcp_query()`** (ping) — calls `_bootstrap()` then `refresh_runtime_from_disk()` again (lines ~79–80).

`health_check` itself also calls `_bootstrap()` at the top (line ~170). The double refresh is harmless but wasteful on a diagnostic path that may run often (Claude Desktop connect, ops checks). Each refresh reloads registry, categories, seed, evicts specialist modules, etc.

**Goal:** Exactly **one** `refresh_runtime_from_disk()` per `health_check()` call, while preserving:

- **One refresh per `query_person`** (via `_run_mcp_query`) — unchanged.
- **One refresh per `list_specialist_routing`** when called as a standalone MCP tool — unchanged.
- All existing `health_check` check semantics (`storage`, `graph`, `lightweight_tool`, `ping_query`, JSON shape, never raises).

---

## Objective

Refactor `src/mycelium_mcp/server.py` so `health_check` performs a single runtime refresh, without duplicating refresh work in its sub-checks.

---

## Proposed approach (implementer discretion on naming)

Prefer **internal helpers without refresh** wrapped by public entry points that refresh:

1. Extract core logic, e.g.:
   - `_routing_payload()` — registry list + JSON dict (no `_bootstrap`, no refresh).
   - `_execute_mcp_query(query_json: str)` — parse, `run_query`, serialize / error recovery (no `_bootstrap`, no refresh). Keep existing recovery/`reset_core_graph` behavior.

2. Public tools stay thin:
   - `list_specialist_routing()` → `_bootstrap()` → `refresh_runtime_from_disk()` → serialize `_routing_payload()`.
   - `_run_mcp_query()` → `_bootstrap()` → `refresh_runtime_from_disk()` → `_execute_mcp_query()`.
   - `query_person` unchanged (still calls `_run_mcp_query`).

3. `health_check()`:
   - `_bootstrap()` once.
   - `refresh_runtime_from_disk()` **once** (after bootstrap).
   - `lightweight_tool` check: call `_routing_payload()` directly (or equivalent), not `list_specialist_routing()`.
   - `ping_query` check: call `_execute_mcp_query(...)` directly, not `_run_mcp_query(...)`.
   - Leave `storage` / `graph` checks as-is.

**Do not** add global flags, thread-locals, or env vars to skip refresh — explicit helper split is clearer and testable.

---

## Tests

Add a **smoke** test (new file or extend `tests/test_mcp_runtime_reload.py`):

- Patch `agents.runtime.refresh_runtime_from_disk` (or `mycelium_mcp.server.refresh_runtime_from_disk` if imported there).
- Call `health_check()` once.
- Assert `refresh_runtime_from_disk` was called **exactly once**.

Optional second smoke: standalone `list_specialist_routing()` still calls refresh exactly once (regression guard).

Run:

```bash
uv run pytest -m smoke -q tests/test_mcp_runtime_reload.py
uv run ruff check src tests
```

Manual smoke (document in `output.md`):

```bash
uv run python -c "
from mycelium_mcp.server import health_check, list_specialist_routing, query_person
import json
h = json.loads(health_check())
assert h.get('status') in ('ok', 'degraded')
assert 'checks' in h
print('health_check:', h['status'], h['checks'])
"
```

---

## Scope boundaries (strict)

**May modify:**
- `src/mycelium_mcp/server.py`
- `tests/test_mcp_runtime_reload.py` or new `tests/test_mcp_health_check.py`

**Out of scope:**
- Changing `refresh_runtime_from_disk()` semantics in `src/agents/runtime.py`
- Graph topology, `PersonQuery`, research, specialist templates
- README / architecture docs (unless one-line comment in server docstring is needed)
- `TODO.md` (Grok updates after review)

---

## Workflow

Per `prompts/cursor/WORKFLOW.md`:

1. Claim this file: move from `prompts/cursor/next/` → `prompts/cursor/in-progress/` **before** any edits.
2. Implement, test, commit with a clear message.
3. Deliver under `prompts/cursor/done/2026-06-06-0900-mcp-health-check-dedupe/`:
   - `prompt.md` (copy of this file)
   - `output.md` — approach, files changed, test output, manual smoke result
4. Remove **only** your claimed file from `in-progress/`.

---

## Success criteria

- `health_check()` triggers exactly one `refresh_runtime_from_disk()` per call.
- `query_person` / `list_specialist_routing` still refresh once per invocation when called directly.
- `health_check` JSON shape and check keys unchanged; smoke tests green.
- Minimal diff; no behavior change beyond deduping refresh on the health path.
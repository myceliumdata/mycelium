# Task: MCP runtime reload — fresh disk state per query

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md` (public interfaces, graph flow, runtime gitignored data)
- `src/mycelium_mcp/server.py` (long-lived stdio server, `_bootstrap`, `_run_mcp_query`)
- `src/main.py` (CLI resets `reset_storage()` + `reset_core_graph()` each invocation)
- `tests/conftest.py` (session cleanup tuple of `reset_*` helpers)

**Depends on:** README documents MCP restart workaround (June 2026); `TODO.md` near-term item **MCP singleton reload**.

---

## Problem (why this slice exists)

The **CLI** starts a **new OS process** on every `mycelium query`. Singletons (`get_agent_registry()`, `get_category_tree()`, `get_seed_data()`, dynamically imported `*_specialist` modules) are empty at import time and **load current files from disk** on first use.

The **MCP server** (`uv run mycelium-mcp`) is a **single long-lived process**. `_bootstrap()` only calls `load_dotenv()` and `get_storage()`. It does **not** refresh:

| Singleton / cache | Risk when stale |
|-------------------|-----------------|
| `AgentRegistry` (`data/agent_registry.json`) | `build_context` iterates `registry.list_agents()` — empty in-memory registry **ignores specialist storage on disk** (email found via CLI but missing in MCP). |
| `CategoryTree` (`data/categories.json`) | New attribute mappings from CLI/classify not visible. |
| `SeedData` (`get_seed_data()`) | Stale seed if `data/seed.json` replaced. |
| `sys.modules` entries for `dyn_specialist_*` / `agents.specialists.*_specialist` | Old specialist code after factory regen. |
| Per-module `_storage` in generated specialists | Cleared when module is evicted and re-imported. |

Today Paul must **restart the MCP client/server** after registry, `.env`, or research-cache changes. That should not be required for normal dev.

**Do not** reset `reset_core_graph()` on every successful query unless you measure unacceptable staleness — MCP uses the sync checkpointer for `thread_id` continuity. Reserve graph reset for the existing error-recovery path in `_run_mcp_query`. (CLI resets graph because it exits immediately.)

---

## Objective

Before each MCP **`query_person`** (and the internal ping inside **`health_check`**), **refresh runtime state from disk** so MCP behavior matches a fresh CLI process for registry, classification cache, seed, and dynamically loaded specialist modules.

---

## Proposed approach (implementer discretion on naming/placement)

1. Add a small helper, e.g. `refresh_runtime_from_disk()` in `src/mycelium_mcp/server.py` **or** `src/agents/runtime.py` (if cleaner for testing imports):
   - `load_dotenv(override=True)` (or project-consistent dotenv behavior)
   - `get_agent_registry().reload()` (already exists on `AgentRegistry`)
   - `get_category_tree().reload()` (already exists on `CategoryTree`)
   - `reset_seed_data()` then touch `get_seed_data()` so seed reloads on next lookup
   - `reset_agent_factory()` so factory re-binds cleanly (optional if reload in-place is sufficient — verify)
   - Evict cached specialist modules: remove `sys.modules` keys matching `dyn_specialist_*` and generated `agents.specialists.*_specialist` (do **not** evict `agents.specialists.base` / `__init__`)

2. Call the helper at the start of `_run_mcp_query` **after** `_bootstrap()` (merge into one path if redundant).

3. Update MCP tool instructions string if it still tells users to restart for registry changes — note automatic reload instead.

4. **README** — shorten “Restart MCP after…” to “restart only if reload fails or after code deploy” (one sentence).

5. **Tests** (smoke, mocked where possible):
   - New `tests/test_mcp_runtime_reload.py` (or extend existing MCP test file if one exists):
     - Write a temp `agent_registry.json` with a fake generated agent entry; set `MYCELIUM_AGENT_REGISTRY_PATH`; call refresh helper; assert `get_agent_registry().has_agent(...)`.
     - Or: seed registry singleton empty, write disk registry with `contact_specialist`, refresh, assert `list_agents()` non-empty.
   - Keep tests isolated with env overrides + `reset_*` in fixture teardown (mirror `test_specialist_research_integration`).

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests
```

**Manual (document in `output.md`):**
1. Start MCP (`uv run mycelium-mcp`) — leave running.
2. In another terminal: `uv run mycelium query --person-key "Andrea Kalmans" --attributes email` (populates registry + storage).
3. Without restarting MCP, call `query_person` with same person + `requested_attributes: ["email"]` via MCP client or `uv run python -c` invoking `_run_mcp_query`.
4. Assert MCP `results` include `email` when CLI did (keys permitting).

---

## Scope boundaries (strict)

**May modify:**
- `src/mycelium_mcp/server.py`
- New small module under `src/agents/` if needed (e.g. `runtime.py`)
- `tests/test_mcp_runtime_reload.py` (or equivalent)
- `README.md` (MCP restart sentence only)

**Out of scope:**
- Changing graph topology, `PersonQuery`, research runner, specialist template
- `reset_core_graph()` on every happy-path query
- LangSmith / Studio / factory auto_commit behavior
- `TODO.md` (Grok will update after review)

---

## Deliverables

Per `WORKFLOW.md`, after claiming this file to `in-progress/`:

```
prompts/cursor/done/2026-06-05-1200-mcp-runtime-reload/
  prompt.md
  output.md
  review.md   # Grok adds after review
```

`output.md` must include: approach summary, files changed, test commands + outputs, manual MCP/CLI parity steps, any tradeoffs (graph/checkpointer left intact).

---

## Success criteria

- MCP `query_person` sees registry/specialist storage written by a concurrent CLI process **without** MCP restart.
- Smoke tests green; no new full-suite requirement unless you add `@pytest.mark.full` (then run it once and document).
- Minimal diff; explicit code; match existing `reset_*` / `reload()` patterns.
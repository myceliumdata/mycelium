# Mycelium — Full Top-Down Code Walkthrough (June 2026)

**Purpose:** Orientation for how the pieces fit together after the **query-only public interface** refactor and introduction of **`core_data_agent`**.

**Current reality (June 2026):**

- **Public API** = queries only (`PersonQuery`: `person_key`, `requested_attributes`). No CLI `ingest`, no MCP `submit_person_data`, no `provided_data`.
- **`core_data_agent`** (`src/agents/core_data.py`) is the specialist that owns core lookups; graph wiring from supervisor → core_data is pending (1070/1100). Routing still performs lookups inline today.
- **enrich/validator** may still be compiled into the graph but are **not** used for public requests; removal is task 1070.
- See `docs/architecture.md` for the authoritative architecture; this doc is a walkthrough.

---

## 1. High-level vision

From `docs/architecture.md` and `prompts/system/CORE_PROMPT.md`:

- AI-managed data infrastructure; external agents use MCP/CLI JSON.
- Supervisor = thin coordinator/router; specialists own domains.
- Phase 1: shared SQLite for core `people` only; `CoreIdentity` facade behind `core_data_agent`.

---

## 2. Project structure & workflow

- Handoffs: `prompts/cursor/next/` → `in-progress/` → `done/<slug>/` (see `prompts/cursor/WORKFLOW.md`).
- `src/agents/`: `supervisor`, `routing`, `responses`, `core_data`, `core_identity`, legacy `enrich`/`validator`.
- `src/graphs/core.py`, `src/models/state.py`, `src/storage/core.py`, `src/mycelium_mcp/server.py`, `src/main.py`.

---

## 3. Data model & contracts (`src/models/state.py`)

- **`Person`**: `id`, `name`, `employer` only.
- **`PersonQuery`** (query-only): `person_key`, `requested_attributes`. No `provided_data`.
- **`PersonResponse`**: `results`, `message`, `debug`, `trace_id`, `thread_id`.
- **`MyceliumGraphState`**: `query` required at input; internal fields (`route`, `person`, `response`, validation*, `audit_log`, invocation ids).

Example response outcomes in `debug`: `outcome='found'`, `'not_found'`, `'non_core_requested'`.

---

## 4. Entry points

| Surface | Commands / tools |
|---------|------------------|
| **CLI** | `uv run mycelium query ...`, `uv run mycelium seed ...` |
| **MCP** | `query_person`, `list_specialist_routing`; schemas via resources |
| **Studio** | `langgraph dev` via `./bin/run-studio` + optional ngrok |

Both CLI and MCP call `graphs.core.run_query` → async graph via `ainvoke` (sync bridge inside `run_query`).

Package: `mycelium_mcp` (renamed from `mcp` to avoid SDK collision).

---

## 5. Graph runtime (`src/graphs/core.py`)

**Compiled today (transitional):** `supervisor` → conditional → `enrich` → `validator` → `supervisor` loop *or* END.

**Public query path today:** `START → supervisor → END` (lookup logic inside supervisor/routing; enrich/validator not visited).

**Target (1070/1100):** `START → supervisor → core_data_agent → END` (drop enrich/validator from graph).

- **Async:** `AsyncSqliteSaver` + async nodes for LangGraph dev / ASGI.
- **`run_query`:** seeds `invocation_thread_id`, `ainvoke`, captures `trace_id`, `_finalize_response`.

---

## 6. Supervisor & routing

- **`supervisor_agent`**: async; `asyncio.to_thread(evaluate_supervisor_turn, ...)`.
- **`evaluate_supervisor_turn`**: query-only — `find_by_key` → found / not-found / non-core responses via `responses.py`.
- No `route_enrich`, no `provided_data`, no ingest response builders.

---

## 7. Core data specialist (`src/agents/core_data.py`)

```python
async def core_data_agent(state) -> dict[str, Any]:
    # find_by_key via CoreIdentity in to_thread
    # sets person, response, audit_log
```

This is the **proper graph node** for core CRM lookups. Not yet the default path in the compiled graph (supervisor/routing still inline). Tests: `tests/test_core_data_agent.py`.

---

## 8. CoreIdentity facade (`src/agents/core_identity.py`)

Thin wrapper over `storage.core.get_storage()`: `find_by_key`, `persist`. Used by `core_data_agent` and routing until wiring is complete.

---

## 9. Storage (`src/storage/core.py`)

SQLite `people(id, name, employer)`; seed from `data/seed_crm.json` on first `get_storage()`.

---

## 10. Response builders (`src/agents/responses.py`)

Query-only: `response_found`, `response_not_found`, `response_non_core`. Not-found messages do **not** suggest public ingest.

---

## 11. Observability

- `trace_id` / `thread_id` on every `PersonResponse` (set in `run_query`).
- `get_langsmith_trace_url()` in `src/utils/langsmith.py`; CLI prints URL when `trace_id` present.

---

## 12. Query flow (end-to-end)

```
CLI/MCP → PersonQuery → run_query → graph.ainvoke
  → supervisor (routing: CoreIdentity.find_by_key)
  → PersonResponse (+ thread_id, trace_id)
```

Future:

```
supervisor → core_data_agent → PersonResponse
```

---

## 13. Historical: public ingest path (removed June 2026)

Previously: `provided_data` on `PersonQuery`, CLI `ingest`, MCP `submit_person_data`, supervisor → enrich → validator → persist.

Removed in tasks `2026-06-05-1000`–`1050`. Will return via **internal** specialist coordination — see architecture.md "Future work: re-adding core data addition".

---

## 14. Gaps / next tasks

- Wire `core_data_agent` in graph (1070, 1100).
- Remove enrich/validator nodes (1070).
- Docs/tests final pass (1080, 1110).
- Real non-core specialists, LangSmith E2E in `.env`, license, CI.

See `TODO.md`.

---

## 15. Mental model

```
External (CLI/MCP) → PersonQuery → run_query → LangGraph
  → supervisor (coordinator)
       → [today] routing + CoreIdentity inline
       → [target] route to core_data_agent
  → PersonResponse
CoreIdentity → CoreStorage → SQLite
```

---

## Local Debugging Tool: LangSmith Studio (LangGraph Studio)

As mentioned when discussing LangSmith setup, for visual debugging of the exact graph:

**Key distinction (this addresses the "why does it need the internet?" question):**

- `langgraph dev` runs the **backend** — Mycelium graph code (supervisor, core data path, storage, state machine) — **locally**.
- **Studio** is the visual UI at `smith.langchain.com/studio`.
- A tunnel (ngrok) bridges local server ↔ hosted UI.

**For offline debugging:**

1. **Direct Python** — `graph.ainvoke` + `asyncio.run` (see README / earlier examples).
2. **Local server only** — `langgraph dev --host 127.0.0.1` without tunnel.

**Studio input forms:** Driven by Pydantic schemas from the running dev server. After editing `src/models/state.py`, **restart** `langgraph dev` (and ngrok) — reload alone is not enough.

Use query-only `MyceliumGraphState` inputs: `{ "query": { "person_key": "...", "requested_attributes": [] } }`. Set `thread_id` in Studio Thread/Config, not inside `PersonQuery`.

Tunnel troubleshooting: see README "Local Debugging with LangSmith Studio".

---

*Last major refresh: June 2026 (query-only public API, core_data_agent, doc task 1090).*

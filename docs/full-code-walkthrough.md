# Mycelium — Full Top-Down Code Walkthrough (June 2026)

**Purpose:** Orientation for how the pieces fit together after the **query-only public interface** refactor and **`core_data_agent`** wiring (tasks 1070/1100/1110, polish 1120).

**Current reality (June 2026):**

- **Networks (roadmap):** Product model is framework + user-chosen **network roots** (see `docs/plans/networks-terminology.md`). Runtime still uses flat `data/` as the prototype default until Phase 2 path resolver lands.
- **Public API** = queries only (`PersonQuery`: `person_key`, `requested_attributes`). No CLI `ingest`, no MCP `submit_person_data`, no `provided_data`.
- **`core_data_agent`** (`src/agents/core_data.py`) owns core lookups in the compiled graph: `supervisor` → `core_data` → END.
- **enrich/validator/person_prep** remain on disk as unwired legacy; not in `agents.__init__` or the public graph.
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
- `src/agents/`: `supervisor`, `routing`, `responses`, `core_data`, `core_identity`, legacy `enrich`/`validator`/`person_prep` (unwired).
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
| **CLI** | `uv run mycelium query ...`, `uv run mycelium seed ...` (now exits promptly after result) |
| **MCP** | `query_person`, `list_specialist_routing`; schemas via resources |
| **Studio** | `langgraph dev` via `./bin/run-studio` + optional ngrok |

Both CLI and MCP call `graphs.core.run_query` → async graph via `ainvoke` (sync bridge inside `run_query`).

Package: `mycelium_mcp` (renamed from `mcp` to avoid SDK collision).

---

## 5. Graph runtime (`src/graphs/core.py`)

**Achieved (1070/1100, finalized 1110):** `START → supervisor → core_data_agent → END`.

- **Supervisor** sets `route="core_data"` and audit entries; no storage access or `PersonResponse` construction.
- **core_data** runs lookup via `CoreIdentity.find_by_key` (0/1/N matches) and sets `response` with plural-aware messages when names are ambiguous.
- **Async:** `AsyncSqliteSaver` + async nodes for LangGraph dev / ASGI.
- **`run_query`:** seeds `invocation_thread_id`, `ainvoke`, captures `trace_id`, `_finalize_response`.
- Checkpoint serde: `JsonPlusSerializer(allowed_msgpack_modules=...)` for `models.state` types in `_setup_async_checkpointer`.

*Historical (pre-1110):* enrich/validator loop was compiled for public ingest; removed from the graph in 1070.

---

## 6. Supervisor & routing

- **`supervisor_agent`**: thin async coordinator; returns `route="core_data"` and audit log only.
- **`evaluate_supervisor_turn`** (`routing.py`): shared lookup/classification helpers — used inside `core_data_agent` and by unit tests (not called directly from the supervisor node).
- **`responses.py`**: query-only builders (`response_found`, `response_not_found`, `response_non_core`).

---

## 7. Core data specialist (`src/agents/core_data.py`)

```python
def core_data_agent(state) -> dict[str, Any]:
    # CoreIdentity.find_by_key → list[Person]; sets persons, response, audit_log
    # person set only when exactly one match
```

Default LangGraph node for core CRM lookups. Tests: `tests/test_core_data_agent.py`, `tests/test_core_graph.py::test_graph_invokes_supervisor_then_core_data`.

---

## 8. CoreIdentity facade (`src/agents/core_identity.py`)

Thin wrapper over `storage.core.get_storage()`: `find_by_key` → `find_persons` (id: 0/1; name: 0..N). Used by `core_data_agent`.

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
  → supervisor (route="core_data")
  → core_data_agent (routing + CoreIdentity.find_by_key)
  → PersonResponse (+ thread_id, trace_id)
```

---

## 13. Historical: public ingest path (removed June 2026)

Previously: `provided_data` on `PersonQuery`, CLI `ingest`, MCP `submit_person_data`, supervisor → enrich → validator → persist.

Removed in tasks `2026-06-05-1000`–`1050`. Graph loop removed in 1070. Will return via **internal** specialist coordination — see architecture.md "Future work: re-adding core data addition".

---

## 14. Gaps / next tasks

From `TODO.md` (near term):

- Continue reducing inline routing lookups in `routing.py` now that `core_data_agent` owns lookups.
- Further narrow response construction or move behind specialist-specific builders.
- **Re-adding data addition** (internal / future): design internal coordination, persist on `core_data_agent`, stronger validation.
- LangSmith E2E verification in operator `.env`.
- License, CI workflows, real non-core specialists.

See `TODO.md` for the full prioritized list.

---

## 15. Mental model

```
External (CLI/MCP) → PersonQuery → run_query → LangGraph
  → supervisor (coordinator, route="core_data")
  → core_data_agent (lookup + PersonResponse)
CoreIdentity → CoreStorage → SQLite
```

---

## Local Debugging Tool: LangSmith Studio (LangGraph Studio)

**Key distinction:**

- `langgraph dev` runs the graph **locally**.
- **Studio** UI at `smith.langchain.com/studio`; ngrok bridges local server ↔ hosted UI.

**For offline debugging:** direct `graph.ainvoke` or `langgraph dev --host 127.0.0.1` without tunnel.

**Studio input forms:** Driven by Pydantic schemas from the running dev server. After editing `src/models/state.py`, **restart** `langgraph dev` — see `tmp/restart-server-for-schema.md`.

Use query-only `MyceliumGraphState`: `{ "query": { "person_key": "...", "requested_attributes": [] } }`. Set `thread_id` in Studio Thread/Config, not inside `PersonQuery`. Examples: `tmp/studio-inputs.md`.

---

*Last major refresh: June 2026 (query-only public API, core_data_agent wired, niggle cleanup 1120).*

# Mycelium — Full Top-Down Code Walkthrough (June 2026)

**Purpose:** Orientation for how the pieces fit together after the **query-only public interface** refactor, **seed-data-context graph**, and **Networks Phases 1–4**.

**Current reality (June 2026):**

- **Networks:** Framework repo + user-chosen **`network_root`** paths. Committed CRM example at `examples/networks/crm/`; bootstrap with `./bin/refresh-example-network crm`. See `docs/plans/networks-terminology.md`.
- **Public API** = queries only (`EntityQuery`: `entity_key`, `requested_attributes`). No CLI `ingest`, no MCP `submit_person_data`, no `provided_data`.
- **Graph:** `supervisor` → `build_context` → `invoke_specialists` → `assemble_response` (or direct assemble for name-only / not found). Identity from `entities.json` + specialist storage.
- See `docs/architecture.md` for the authoritative architecture; this doc is a walkthrough.

---

## 1. High-level vision

From `docs/architecture.md` and `prompts/system/CORE_PROMPT.md`:

- AI-managed data infrastructure; external agents use MCP/CLI JSON.
- Supervisor = thin coordinator/router; generated specialists own non-core domains.
- Optional bootstrap `seed.json` at `<network_root>/`; canonical store is `entities.json` (import on refresh/create; query-time binds).

---

## 2. Project structure & workflow

- Handoffs: `prompts/cursor/next/` → `in-progress/` → `done/<slug>/` (see `prompts/cursor/WORKFLOW.md`).
- `src/network/`: path resolver, name registry, `network_metadata` for MCP `health_check`.
- `src/agents/`: `supervisor`, `dispatch`, `classification`, `factory`, `entity_registry`.
- `src/graphs/core.py`, `src/models/state.py`, `src/storage/core.py`, `src/mycelium_mcp/server.py`, `src/main.py`.

---

## 3. Data model & contracts (`src/models/state.py`)

- **`IdentityRecord`**: `id`, `name`, `employer` only.
- **`EntityQuery`** (query-only): `entity_key`, `requested_attributes`. No `provided_data`.
- **`QueryResponse`**: `results`, `message`, `debug`, `trace_id`, `thread_id`.
- **`MyceliumGraphState`**: `query` required at input; internal fields (`route`, `identity_record`, `response`, `audit_log`, classifications, etc.).

---

## 4. Entry points

| Surface | Commands / tools |
|---------|------------------|
| **CLI** | `mycelium query`, `mycelium network …` |
| **MCP** | `describe_network`, `query_entity`, `health_check`; schemas via resources |
| **Studio** | `langgraph dev` via `./bin/run-studio` + optional ngrok |

Both CLI and MCP call `graphs.core.run_query` after resolving `network_root` (CLI per invocation; MCP at bootstrap + reload).

Package: `mycelium_mcp` (renamed from `mcp` to avoid SDK collision).

---

## 5. Graph runtime (`src/graphs/core.py`)

**Current:** `START → supervisor → build_context → invoke_specialists → assemble_response → END`  
(or `supervisor → assemble_response` when name-only / not found).

- **Supervisor** resolves registry matches, classifies attributes, plans specialist invocations.
- **build_context** unions registry identity + specialist storage for matched id(s).
- **invoke_specialists** runs generated specialists (sync research on cache miss when keys set).
- **assemble_response** builds unified `QueryResponse`.
- **Checkpointer:** async path (Studio); sync path forced for MCP/CLI (`MYCELIUM_USE_SYNC_CHECKPOINTER`).

---

## 6. Entity registry + bootstrap import

- **`entities.json`** — canonical runtime store (`EntityRegistry`, `lookup_entities_by_key`).
- **`network/seed_import.py`** — imports optional `seed.json` rows at bootstrap (refresh/create) via `ensure_bound_entity`.
- Query-time resolution: `resolve_entity` / `lookup_entities_by_key` (registry only).

Committed examples: `examples/networks/crm/` (bootstrap seed), `examples/networks/empty-crm/` (no seed, growth from queries).

---

## 7. Supervisor, dispatch, factory

- **`supervisor_agent`**: registry resolution, classification, specialist planning, routing audit.
- **`dispatch`**: `build_context`, `invoke_specialists`, `assemble_response` nodes.
- **`factory`**: Jinja template → generated `*_specialist.py` under `src/agents/specialists/` (gitignored).
- **`classification`**: attribute → category map (`categories.json` under network root).

---

## 8. Storage (`src/storage/core.py`)

SQLite `people(id, name, employer)` retained for checkpoints-era compatibility; **queries** use `entities.json` + specialist files, not auto SQLite seeding.

Paths resolve under active `network_root` via `src/network/paths.py`.

---

## 9. MCP server (`src/mycelium_mcp/server.py`)

- One long-lived process per network (`MYCELIUM_NETWORK_ROOT` or `MYCELIUM_NETWORK`).
- `health_check` returns `info.network_root`, `network_name`, `network_display_name`.
- `refresh_runtime_from_disk()` before each query.

---

## 10. Query flow (end-to-end)

```
CLI/MCP → resolve network_root → EntityQuery → run_query → graph.ainvoke
  → supervisor
  → build_context (if specialists needed)
  → invoke_specialists
  → assemble_response
  → QueryResponse (+ thread_id, trace_id)
```

---

## 11. Historical notes

- **Public ingest** (CLI `ingest`, `provided_data`) removed June 2026.
- **`core_data_agent` graph** replaced by seed-data-context flow (supervisor + specialists).
- **Flat `data/seed_crm.json`** prototype removed; see `examples/networks/crm/` and git tag `prototype`.

---

## 12. Gaps / next tasks

From `TODO.md`:

- Networks Phases 1–5 delivered (`network create`, per-network `specialists/`, skeleton ontology).
- Query-as-seed launch (v2), inter-network handoff (Phase 6).
- LangSmith E2E verification in operator `.env`.

---

## Mental model

```
External (CLI/MCP) → network_root → EntityQuery → run_query → LangGraph
  → supervisor → specialists → assemble_response
entities.json + Specialist storage (agents/<category>/) under network_root
```

---

*Last major refresh: June 2026 (networks Phases 1–4, seed-data-context graph, MCP network metadata).*

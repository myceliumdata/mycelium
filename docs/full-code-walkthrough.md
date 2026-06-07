# Mycelium — Full Top-Down Code Walkthrough (June 2026)

**Purpose:** Orientation for how the pieces fit together after the **query-only public interface** refactor, **seed-data-context graph**, and **Networks Phases 1–4**.

**Current reality (June 2026):**

- **Networks:** Framework repo + user-chosen **`network_root`** paths. Committed CRM example at `examples/networks/crm/`; legacy repo `data/` is an empty shim until bootstrap (`bin/copy-example-network`). See `docs/plans/networks-terminology.md`.
- **Public API** = queries only (`PersonQuery`: `person_key`, `requested_attributes`). No CLI `ingest`, no MCP `submit_person_data`, no `provided_data`.
- **Graph:** `supervisor` → `build_context` → `invoke_specialists` → `assemble_response` (or direct assemble for name-only / not found). Identity from `agents.seed` + specialist storage.
- **Legacy on disk:** `core_data`, `core_identity`, `enrich`/`validator`/`person_prep` — unwired; not in the public graph.
- See `docs/architecture.md` for the authoritative architecture; this doc is a walkthrough.

---

## 1. High-level vision

From `docs/architecture.md` and `prompts/system/CORE_PROMPT.md`:

- AI-managed data infrastructure; external agents use MCP/CLI JSON.
- Supervisor = thin coordinator/router; generated specialists own non-core domains.
- Seed JSON at `<network_root>/seed.json`; stable UUIDs assigned at load time (`agents/seed.py`).

---

## 2. Project structure & workflow

- Handoffs: `prompts/cursor/next/` → `in-progress/` → `done/<slug>/` (see `prompts/cursor/WORKFLOW.md`).
- `src/network/`: path resolver, name registry, `network_metadata` for MCP `health_check`.
- `src/agents/`: `supervisor`, `dispatch`, `classification`, `factory`, `seed`, legacy modules (unwired).
- `src/graphs/core.py`, `src/models/state.py`, `src/storage/core.py`, `src/mycelium_mcp/server.py`, `src/main.py`.

---

## 3. Data model & contracts (`src/models/state.py`)

- **`Person`**: `id`, `name`, `employer` only.
- **`PersonQuery`** (query-only): `person_key`, `requested_attributes`. No `provided_data`.
- **`PersonResponse`**: `results`, `message`, `debug`, `trace_id`, `thread_id`.
- **`MyceliumGraphState`**: `query` required at input; internal fields (`route`, `person`, `response`, `audit_log`, classifications, etc.).

---

## 4. Entry points

| Surface | Commands / tools |
|---------|------------------|
| **CLI** | `mycelium query`, `mycelium network …`, `mycelium seed` (legacy SQLite load) |
| **MCP** | `query_person`, `list_specialist_routing`, `health_check`; schemas via resources |
| **Studio** | `langgraph dev` via `./bin/run-studio` + optional ngrok |

Both CLI and MCP call `graphs.core.run_query` after resolving `network_root` (CLI per invocation; MCP at bootstrap + reload).

Package: `mycelium_mcp` (renamed from `mcp` to avoid SDK collision).

---

## 5. Graph runtime (`src/graphs/core.py`)

**Current:** `START → supervisor → build_context → invoke_specialists → assemble_response → END`  
(or `supervisor → assemble_response` when name-only / not found).

- **Supervisor** resolves seed matches, classifies attributes, plans specialist invocations.
- **build_context** unions seed + specialist storage for matched person id(s).
- **invoke_specialists** runs generated specialists (sync research on cache miss when keys set).
- **assemble_response** builds unified `PersonResponse`.
- **Checkpointer:** async path (Studio); sync path forced for MCP/CLI (`MYCELIUM_USE_SYNC_CHECKPOINTER`).

---

## 6. Seed loader (`src/agents/seed.py`)

- Reads `<network_root>/seed.json` (env `MYCELIUM_SEED_PATH` after path resolver runs).
- Assigns stable UUID per row (uuid5 from name|employer); file holds name + employer only.
- `find_by_key(person_key)` — by UUID or exact name (0..N for ambiguous names).

Committed example: `examples/networks/crm/seed.json`.

---

## 7. Supervisor, dispatch, factory

- **`supervisor_agent`**: seed resolution, classification, specialist planning, routing audit.
- **`dispatch`**: `build_context`, `invoke_specialists`, `assemble_response` nodes.
- **`factory`**: Jinja template → generated `*_specialist.py` under `src/agents/specialists/` (gitignored).
- **`classification`**: attribute → category map (`categories.json` under network root).

---

## 8. Storage (`src/storage/core.py`)

SQLite `people(id, name, employer)` retained for legacy `mycelium seed` and checkpoints-era compatibility; **queries** use JSON seed + specialist files, not auto SQLite seeding.

Paths resolve under active `network_root` via `src/network/paths.py`.

---

## 9. MCP server (`src/mycelium_mcp/server.py`)

- One long-lived process per network (`MYCELIUM_NETWORK_ROOT` or `MYCELIUM_NETWORK`).
- `health_check` returns `info.network_root`, `network_name`, `network_display_name`.
- `refresh_runtime_from_disk()` before each query.

---

## 10. Query flow (end-to-end)

```
CLI/MCP → resolve network_root → PersonQuery → run_query → graph.ainvoke
  → supervisor
  → build_context (if specialists needed)
  → invoke_specialists
  → assemble_response
  → PersonResponse (+ thread_id, trace_id)
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
External (CLI/MCP) → network_root → PersonQuery → run_query → LangGraph
  → supervisor → specialists → assemble_response
Seed (seed.json) + Specialist storage (agents/<category>/) under network_root
```

---

*Last major refresh: June 2026 (networks Phases 1–4, seed-data-context graph, MCP network metadata).*

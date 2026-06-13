# Mycelium — Full Top-Down Code Walkthrough (June 2026)

**Purpose:** Orientation for how the pieces fit together after the **query-only public interface** refactor, **seed-data-context graph**, and **Networks Phases 1–4**.

**Current reality (June 2026 — MVR redesign M1–M10 shipped):**

- **Networks:** Framework repo + user-chosen **`network_root`** paths. Committed CRM example at `examples/networks/crm/`; bootstrap with `./bin/refresh-example-network crm`. See `docs/plans/networks-terminology.md`.
- **Public API** = target two-step protocol (`EntityQuery`: step 1 `id` or `lookup` + optional `requested_attributes`; step 2 `delivery_id` + optional `quote_id`). Legacy `entity_key` / `binding` rejected on CLI, MCP, admin. No CLI `ingest`, no MCP `submit_person_data`.
- **Graph:** `target_resolve` (step 1 or step 2 deliver) → `supervisor` → … → `assemble_response`. Step 1 returns `lookup_resolved` + `delivery_id` (`delivery.create_on_deliver: true` when step 2 will create). Identity from `entities.json` + specialist storage.
- See `docs/architecture.md` for the authoritative architecture; examples in `docs/plans/mvr-redesign-entity-query-examples.md`.

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
- **`EntityQuery`** (target protocol): step 1 — `id` or `lookup`, optional `requested_attributes`, `provenance`; step 2 — `delivery_id`, optional `quote_id`. Legacy `entity_key` internal-only when `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY=1`.
- **`QueryResponse`**: `outcome`, `total_matches`, `delivery`, `quote`, `results`, `message`, `provenance`, `debug`, `trace_id`, `thread_id`. Public JSON via `public_dict()` / `public_json()`.
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

**Current:** `START → target_resolve → supervisor → validate_entity → metering_gate → build_context → invoke_specialists → assemble_response → END`  
(`target_resolve` may short-circuit to `assemble_response` on step-1 `lookup_resolved` / `quote_required` / `not_found`).

- **target_resolve** (`src/agents/dispatch.py`): step-1 lookup/id → `delivery_id`; step-2 deliver hydrates scope (create-on-deliver binds provisional row when flagged).
- **Supervisor** classifies attributes, plans specialist invocations (after deliver scope is loaded).
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
- **`factory`**: Jinja template → generated `*_specialist.py` under `<network_root>/specialists/` (CRM reference copies also under `src/agents/specialists/`).
- **`classification`**: attribute → category map (`categories.json` under network root).

---

## 8. Storage (`src/storage/core.py`)

`mycelium.db` may exist as an optional empty SQLite file for bootstrap compatibility; **no `people` table** (removed June 2026). Identity and queries use `entities.json` + specialist files under `network_root`.

Paths resolve under active `network_root` via `src/network/paths.py` (`deliveries.json`, `quotes.json`, metering stores when enabled).

---

## 9. MCP server (`src/mycelium_mcp/server.py`)

- One long-lived process per network (`MYCELIUM_NETWORK_ROOT` or `MYCELIUM_NETWORK`).
- Tools: `query_entity`, `describe_network`, `pay_quote` (when payment enabled), `health_check`.
- `health_check` returns `info.network_root`, `network_name`, `network_display_name`; internally pings step 1 + step 2 for diagnostics.
- `refresh_runtime_from_disk()` before each query.

---

## 10. Query flow (end-to-end)

```
CLI/MCP/admin → resolve network_root → EntityQuery → run_query → graph.ainvoke
  → target_resolve (step 1: lookup_resolved + delivery_id; step 2: load scope / create)
  → supervisor → validate_entity → metering_gate (if metered)
  → build_context → invoke_specialists (if attrs on step-1 scope)
  → assemble_response
  → QueryResponse.public_dict() (+ thread_id, trace_id)
```

Two-step example: `mycelium query --lookup-json '{…}'` then `mycelium query --delivery-id d_…`. Admin UI mirrors the same explicit two-step flow.

---

## 11. Historical notes

- **Public ingest** (CLI `ingest`, `provided_data`) removed June 2026.
- **`core_data_agent` graph** replaced by seed-data-context flow (supervisor + specialists).
- **Flat `data/seed_crm.json`** prototype removed; see `examples/networks/crm/` and git tag `prototype`.

---

## 12. Gaps / next tasks

From `TODO.md` (June 2026):

- **MVR redesign M1–M10** — shipped (two-step protocol, `DeliveryStore`, admin query UI).
- **Networks Phases 1–5** — delivered (`network create`, per-network `specialists/`, skeleton ontology).
- **Next:** Program 2 (versioned bind storage), query-as-seed launch (v2), inter-network handoff (Phase 6).
- LangSmith E2E verification in operator `.env`.

---

## Mental model

```
External (CLI/MCP) → network_root → EntityQuery → run_query → LangGraph
  → supervisor → specialists → assemble_response
entities.json + Specialist storage (agents/<category>/) under network_root
```

---

*Last major refresh: June 2026 (MVR redesign M1–M10, networks Phases 1–5, target two-step protocol).*

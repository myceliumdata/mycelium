# Mycelium — Architecture & Current Direction

**Status:** Living document (as of June 2026)  
**Purpose:** Current architecture, key decisions, and implementation guidance for the active phase.

> **Note:** This document replaces the previous `docs/vision.md` and `docs/phase-1-direction.md`. The latter two are now considered historical.

---

## Overview

Mycelium is an AI-native data management system in which intelligent agents autonomously organize, evolve, and maintain data sources.

Mycelium organizes people data into **networks**—each network is a scoped ecosystem of specialist agents. Within a network, a **supervisor** coordinates a graph of specialists that classify, research, and persist attributes. (This is the **product network** sense; it is distinct from social/professional **profiles** such as LinkedIn or X handles.)

The framework uses LangGraph agent collectives for ingestion, schema evolution, validation, indexing, and continuous self-improvement — creating living, self-organizing information ecosystems.

**Long-term Vision:**  
Create data infrastructure that is **100% managed by AI**, removing the structural and scalability limitations imposed by human-organized data systems.

---

## Core Motivation

Current data sources are organized by humans for humans. This imposes significant structural and scalability constraints. Mycelium aims to build data infrastructure where AI agents take primary ownership of organization, quality, and evolution.

---

## Target Capabilities

- Autonomous schema inference and evolution
- Intelligent multi-source ingestion
- Continuous data validation and quality control
- Self-optimizing indexing and retrieval patterns
- Emergent discovery of connections across datasets
- Human-in-the-loop only for high-level guidance

---

## Core Architectural Philosophy (Phase 1+)

**Everything is ultimately owned by specialist agents — including the "core" dataset.**

Key implications:

- The **Supervisor** is a **coordinator and router**, not a data owner or direct accessor.
- Specialist agents own both the *responsibility* for a domain of data **and** the storage strategy for that data.
- Even basic **identity resolution** (finding a person by email, X handle, name, etc.) may require querying specialist agents rather than direct database lookups.
- The supervisor detects the type of data being requested, routes to the appropriate specialist agent, and can trigger creation of new agents when needed.
- There are no "god agents." The supervisor must remain narrow and explicit.

This is a deliberate departure from earlier thinking that treated the core CRM table as a privileged, directly-queryable store.

### Public interface: query-only (June 2026)

The **CLI** (`query`) and **MCP** (`describe_network`, `query_entity`, `health_check`) expose **lookups only**. Today `EntityQuery` uses `entity_key` and optional `binding` / `requested_attributes` — no `provided_data` on the public model. **Target:** `id` or `lookup` plus two-step `delivery_id` ([MVR redesign](#mvr-redesign-target-protocol)). MCP **`describe_network`** returns author `guide.md`, ontology categories, framework policy, and the locked target-protocol narrative (runtime unchanged until M2–M9).

Data addition via the public API was removed in the June 2026 refactor (tasks 1000–1050). It will return later as **internal agent coordination**, not as a direct caller-supplied payload.

### Seed bootstrap and identity (June 2026 — seed elimination)

- **Optional fixture:** `<network_root>/seed.json` — static `people` array for bootstrap only (not read at query time). Committed CRM example: `examples/networks/crm/seed.json`. Import via `./bin/refresh-example-network crm` or `mycelium network create` when the file is present (`network/seed_import.py` → `entities.json`).
- **Transform (maintainers):** `examples/networks/crm/prepare_seed.py` builds example `seed.json` from a CRM source file (name + employer only; no legacy `id` in the file). Full prototype data: git tag `prototype`.
- **Runtime store:** `entities.json` holds canonical entities (uuid4 ids, `bind_index`). `ensure_bound_entity` assigns stable ids on import; supervisor resolves lookups via `lookup_entities_by_key` / `resolve_entity` (registry only). **Target:** per-field indexes + `lookup` map resolution (M4); identity references use `id` only (R1).
- **No `core_data` specialist** — identity fields (name, employer) come from the registry; specialists may override them later.

### Supervisor and graph (current)

The **supervisor** (`src/agents/supervisor.py`) resolves registry matches, classifies `requested_attributes`, and plans which generated specialists to invoke. It does **not** build the final response when specialists are needed.

**Graph flow** (`src/graphs/core.py`):

```
START → supervisor → validate_entity → metering_gate → build_context → invoke_specialists → assemble_response → END
              └────────────────────────────────────── assemble_response (blocked / identity-only)
```

### Metering negotiation vs payment settlement (Slice 10–11)

Negotiation and settlement are separate layers. MCP `query_entity` handles priced-commit negotiation; `pay_quote` handles settlement.

```
┌─────────────────────────────────────────────────────────────┐
│ NEGOTIATION (MCP — query_entity)                            │
│   query → quote_required + Quote JSON                       │
│   query + quote_id → work runs (after accept gate)          │
└────────────────────────────┬────────────────────────────────┘
                             │ when metering.payment.enabled
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ SETTLEMENT (pay_quote → PaymentProvider)                    │
│   MockProvider / CreditProvider / X402StubProvider          │
│   quote status: pending → paid → accepted                   │
│   payment_required if quote_id sent before pay_quote        │
└─────────────────────────────────────────────────────────────┘
```

Bypass env vars for tests/demos: `MYCELIUM_AUTO_ACCEPT_QUOTES` (skip metering), `MYCELIUM_AUTO_SETTLE_QUOTES` (skip payment when metering on). CRM example keeps both disabled.

Future real x402 settlement may read `MYCELIUM_X402_FACILITATOR_URL` for facilitator HTTP; the Slice 11 stub provider ignores it (CI uses `x402:test:` proofs only).

- **build_context** (`src/agents/context.py`) — union of registry identity + all specialist storage for the matched `id`(s).
- **invoke_specialists** — each required specialist receives full `context`, `current_id`, and `target_fields` (owned attributes only).
- **assemble_response** — unified `QueryResponse` from registry identity + specialist contributions.

Generated specialists (`src/agents/specialists/*_specialist.py`, Agent Factory template) implement three scenarios: has data, **synchronous** field research on cache miss (when `OPENAI_API_KEY` + `TAVILY_API_KEY` are set), or pending / N/A. Research runs via `tools.research.run_field_research` and Tavily `web_search` (`src/tools/tavily.py`). See `docs/plans/seed-data-context-architecture.md`, `docs/plans/specialist-research-phase1.md`, and Cursor slices `2026-06-09-1100`–`1400`.

Pre–registry ingest (`enrich`, `validator`, `person_prep`) and the SQLite `people` table were removed June 2026. See [`docs/legacy-ingest-and-storage-reference.md`](legacy-ingest-and-storage-reference.md).

---

## Current Data Model (Phase 1 — Strictly Minimal Core)

The core `IdentityRecord` record is deliberately tiny:

```python
class IdentityRecord(BaseModel):
    id: str
    name: str
    employer: str | None = None
```

**Identity rules:**
- Bootstrap seed provides `name`, `employer` only; runtime and public `results["id"]` use the stable UUID from `entities.json` (assigned on import via `ensure_bound_entity`).
- `name` and `employer` are specialist-owned like any other attribute when requested (no privileged core filter).
- There is no `extra` field on `IdentityRecord`.

---

## Derivative / Non-Core Data

Phase 1 adds a **Classification Engine** (cached lookup in `src/agents/classification/`, backed by runtime `<network_root>/categories.json` seeded from `_SEED_CATEGORIES` in `engine.py`; gitignored) that the supervisor uses for non-core `requested_attributes`. Illustrative shape: [`docs/examples/sample-categories.json`](examples/sample-categories.json) (documentation only, not copied to networks). Known attributes are instant map lookups; first-time unknowns may call the LLM once (lazy, structured proposals), then cache—including garbage rejected as `unknown`. Batch tree evolution uses `CategoryTree.refresh_from_llm` (admin/off-path). Metadata flows to `audit_log`, `state.classifications`, and `response.debug` (see `docs/plans/classification-engine-phase1.md`).

**Phase 2 Agent Factory** adds on-demand creation of specialist agents (Jinja2 template in `src/agents/factory/`, runtime `<network_root>/agent_registry.json`, generated `<network_root>/specialists/*_specialist.py` with an AUTO-GENERATED header, and `specialist_dispatcher`). The supervisor triggers `AgentFactory.create_specialist` when classification names an `assigned_agent` that is not yet registered. Each specialist starts with per-category flat JSON plus `storage_strategy.json` hooks for future self-evolution (see `docs/plans/agent-factory-phase2.md`).

- We **explicitly do not pre-define** derivative attributes, dataset types, or storage structures.
- The supervisor classifies requested attributes (lookup only in Phase 1) before routing; real specialist handoff is future work.
- If no suitable agent exists, the system should support creating one.
- How a specialist agent stores and manages its data is not defined centrally.

**Phase 1 Practical Rule:**
- Do not create shared tables or infrastructure for "derivative datasets" in the core storage layer.
- When the supervisor sees non-core attributes, it notes this in the response and audit log rather than creating formal derivative records.

---

## Storage (current)

- **Entities (queries):** `<network_root>/entities.json` via `EntityRegistry` — seed is bootstrap-only when present.
- **Specialists:** per-category JSON under `<network_root>/agents/<category>/` (`SpecialistStorage` in `src/agents/specialists/base.py`), keyed by `id` (UUID). Extended attributes use **`versioned_provenance_v1`**: each field stores `versions[]` + `current_version_id` (append-only provenance). Deprecated flat v1 field blobs are invalid — refresh the network or delete `agents/<category>/storage.json` to reset. Research writes may still **wrap** a legacy flat **pending** blob into versioned `v1` once (`ensure_versioned_for_write`) so in-flight retries can complete; all other flat shapes fail loud on read. Admin `/status` and `mycelium network status --json` expose full `versions[]` per extended field on entity drill-down (bind fields omit history). Admin UI renders version history in a full-width sub-row below each extended field (status badges, short timestamps, `reason` / `last_error`, source links).
- **SQLite:** `<network_root>/checkpoints.sqlite` (LangGraph checkpointer). Optional `<network_root>/mycelium.db` — empty bootstrap file only; no identity tables.

See `src/storage/core.py` (path bootstrap for MCP/admin startup).

---

## Networks (product model — documented June 2026; runtime in Phases 2–4)

Users download the **framework** (this repo: `src/`, `bin/`, docs, tests) and run **named networks** at user-chosen **`network_root`** paths. Network data never has to live inside the clone; it can be on Dropbox, another disk, etc.

| Layer | Location | Notes |
|-------|----------|-------|
| **Framework** | Repo clone | Code, tooling, tests |
| **Network root** | User-chosen directory | All runtime artifacts for one network |
| **Example network** | `examples/networks/` (Phase 4) | Committed reference (e.g. CRM) |
| **Live CRM** | User path (e.g. `~/mycelium-networks/crm`) | Bootstrap via `./bin/refresh-example-network crm` |

**Standard layout under `network_root`** (target contract):

```
<network_root>/
  network.json
  seed.json
  categories.json       # skeleton ontology at create; runtime (see docs/examples/sample-categories.json)
  agent_registry.json
  specialists/          # generated *_specialist.py (Phase 5; per-network)
  agents/<category>/storage.json
  checkpoints.sqlite
  mycelium.db          # optional legacy
```

**Ontology vs classification:** `network create` writes a **skeleton ontology** (categories, specialists, minimal `attribute_map` from examples). The classification engine still **grows `attribute_map` lazily** at query time when clients request attributes not yet mapped.

**Selection (target resolution order):** CLI `--network-dir` → CLI `--network` (name via registry, Phase 3) → env `MYCELIUM_NETWORK_ROOT` → env `MYCELIUM_NETWORK` → **default network** from user config (Phase 3). Unconfigured installs raise a clear error pointing to `./bin/refresh-example-network crm`.

**MCP:** One long-lived stdio process **per network**. Run several MCP servers in parallel by giving each client entry a different `MYCELIUM_NETWORK_ROOT` while `cwd` stays the framework repo. `refresh_runtime_from_disk()` reloads only that process’s network files. No network switching inside a single MCP process.

**Terminology:** Product **network** ≠ LangGraph **agent collective** ≠ social **profiles** (attribute domain). Full map and phased delivery: [`docs/plans/networks-terminology.md`](plans/networks-terminology.md). Pre-networks baseline: git tag `prototype`.

### Framework credentials vs network data (June 2026)

**API keys and provider config are framework-level, not per-network.** One `.env` (or equivalent env block in the MCP client) per machine/operator covers all networks:

| Lives in framework `.env` (process-wide) | Lives under `network_root` (per network) |
|------------------------------------------|------------------------------------------|
| `OPENAI_API_KEY`, `TAVILY_API_KEY`, `ANTHROPIC_API_KEY`, … | `seed.json`, `categories.json`, `agent_registry.json`, `specialists/`, `agents/` |
| `LANGCHAIN_*`, `LANGSMITH_*` (tracing) | `checkpoints.sqlite`, `mycelium.db`, `network.json` |
| `MYCELIUM_RESEARCH_*` tuning | — |

CLI and MCP call `load_dotenv()` at startup from the **framework** working directory. **`MYCELIUM_NETWORK_ROOT`** / **`MYCELIUM_NETWORK`** select which data directory to use; they do not hold secrets. Launching or registering a network does **not** copy or create a `.env` inside `network_root`.

**MCP:** `cwd` = framework repo; per-server `env` sets only network selection (plus the same shared API keys as other servers on that host). Person lookups today use **`entity_key`** against that network’s registry and specialist storage — not env vars. **Target (MVR redesign):** `id` or `lookup` map, then two-step `delivery_id` — see [MVR redesign (target)](#mvr-redesign-target-protocol) below.

Future (not v1): per-network LangSmith project names, optional credential profiles — see `TODO.md`.

---

## MVR redesign (target protocol)

**Status:** Locked design; **runtime still uses legacy `entity_key` / `binding`** until slices M2–M9 ship.  
**Program:** [`docs/plans/mvr-redesign-program.md`](plans/mvr-redesign-program.md) · **Operator guide:** [`docs/plans/mvr-best-practices.md`](plans/mvr-best-practices.md) · **Examples:** [`docs/plans/mvr-redesign-entity-query-examples.md`](plans/mvr-redesign-entity-query-examples.md)

**Program 2** (versioned bind storage / `bind_versions[]`) is **blocked** until this program completes.

### Three separated concerns

| Concern | Meaning |
|---------|---------|
| **Identity** | Stable **`id` (UUID)** only — no name string as primary key |
| **Lookup** | Find candidate rows by **partial field match** (AND within `lookup`) |
| **MVR** | Per-network **minimum field set** to **create** a new entity and **run extended research** |

Today these are conflated in `EntityQuery.entity_key`, `binding`, and `network.json` `mvr.name_source`. The redesign removes `entity_key`, `binding`, and `name_source`.

### Two-step delivery (like quotes)

1. **Step 1 — Resolve:** send `id` **or** `lookup` (AND within map); optional `requested_attributes` and `provenance` **on this step only**. Response: `total_matches`, empty `results[]`, and `delivery.delivery_id` (+ `quote` when `metering.enabled`).
2. **Step 2 — Deliver:** send `delivery_id` (+ `quote_id` when metered). Response: `assembled` / `found` with full `results[]` (and research when attrs were bound on step 1).

No `deliver: true` flag. `delivery_id` and `quote_id` TTL default **5 minutes** (`MYCELIUM_DELIVERY_TTL_SEC`, `MYCELIUM_QUOTE_TTL_SEC`).

### Target `EntityQuery` fields

| Field | Step | Role |
|-------|------|------|
| `id` | 1 | UUID — resolve one entity (still returns `delivery_id`) |
| `lookup` | 1 | `{ field: value }` — AND match; keys ⊆ `mvr.bind_fields` |
| `requested_attributes` | 1 only | Extended attrs; bound into `delivery_id` / quote workload |
| `provenance` | 1 only | Bound into delivery scope |
| `delivery_id` | 2 | From step 1 |
| `quote_id` | 2 | When metering accepted |

**Removed:** `entity_key`, `binding`. **`name_source`** removed from `network.json` — `name` is a normal MVR field in `lookup` and stored rows.

### Target outcomes

| Outcome | When |
|---------|------|
| `lookup_resolved` | Step 1; count + `delivery_id`; free delivery available |
| `quote_required` | Step 1; metering on; need `quote_id` + `delivery_id` to deliver |
| `not_found` | 0 matches, unknown `id`, or expired/invalid tokens |
| `assembled` / `found` | Step 2 delivery (and research when attrs bound) |

Legacy outcomes (`entity_unknown`, `entity_key_unresolved`, `entity_bound_provisional`, …) are retired with the old protocol in M7–M9.

### Create flow (0 matches)

Partial `lookup` with 0 matches → `not_found` (no create). Full MVR in step-1 `lookup` + `requested_attributes` → provisional create on deliver path (slice M7). See program doc for batch and metering rules.

### Indexes (target)

One inverted index per MVR field on `entities.json` (normalized value → `[uuid, …]`). Compound indexes deferred (Program 2 / operator).

---

## Public query flow (current runtime)

Core storage holds only `id`, `name`, and `employer`. Callers send a query-only **`EntityQuery`** (`entity_key`, optional `binding`, optional `requested_attributes`). The graph state always includes `MyceliumGraphState.query`; LangSmith trace input therefore always shows a `query` section even for internal-only operations.

> **Migration:** This section describes **today’s** protocol. Implementers and MCP clients should plan for the [MVR redesign (target protocol)](#mvr-redesign-target-protocol) above.

### Flow summary

| Intent | What the caller sends | Graph path (current / target) | What comes back |
|--------|----------------------|-------------------------------|-----------------|
| **Lookup (found)** | `entity_key` only | `supervisor` → `assemble_response` (seed) | `results`: identity dict(s) from seed; `message`: "Found record for …" |
| **Lookup (miss)** | unknown `entity_key` | `supervisor` → `assemble_response` | `results`: `[]`; not-found `message` |
| **Non-core attrs** | `entity_key` + attrs | `supervisor` → `build_context` → `invoke_specialists` → `assemble_response` | `results`: `id` + requested attrs (merged); `message`: classification-aware per-attribute status (found values omitted; researching / unavailable / out-of-scope sentences) |

### Response fields (query outcomes)

All external responses use the minimalist **`QueryResponse`** (`results`, `message`, `provenance`, `debug`, `trace_id`, `thread_id`):

- **`results`** — One dict per match. Always includes `"id"` (stable UUID). With no `requested_attributes`: `id`, `name`, `employer`. With `requested_attributes`: `id` plus only those keys after specialist-first merge (specialist value wins; seed provisional while pending). No `person_id` field.
- **`message`** — Primary channel: found / not-found / per-attribute status. Visiting agents read natural-language sentences built from supervisor classifications: **researching** (in-scope, pending), **unavailable** (researched, no value), **out_of_scope** (`category == "unknown"` — never "researching" wording). Found attribute values appear only in `results`, not repeated in `message`. Multi-match uses a collective prefix (`Found N records for 'key'.`).
- **`provenance`** — Optional structured version history. **`EntityQuery.provenance`** (request flag, default `false`) controls whether this block is populated; it is unrelated to the response field name. When `true` and the outcome delivers results (`assembled` / `found`) with requested extended attributes, `provenance.entities[]` lists each match `id` and per-attribute `current_version_id` + `versions[]` copied from specialist storage (bind fields `name` / `employer` omitted). Default flat `results[]` is unchanged. Metering may charge a `query_provenance` line when enabled. See [`attribute-provenance-program1.md`](plans/attribute-provenance-program1.md).
- **`debug`** — Internal context (original `entity_key`, `requested_attributes`, outcome tags). Callers should not depend on it.
- **`trace_id`** — LangSmith trace identifier for this graph invocation when `LANGCHAIN_TRACING_V2` is enabled; otherwise `null`. Lets operators and developers jump from a JSON response to the matching trace in LangSmith for debugging. When creating your LangSmith API key, select **Personal Access Token (PAT)** (prefix `lsv2_pt_`). `LANGCHAIN_PROJECT` (default "mycelium") names the tracing project in the LangSmith UI — it will be created automatically on first use; no manual pre-creation required. See README.md for full setup steps.
- **`thread_id`** — Conversation/session identifier for this request. CLI and MCP callers may pass a stable `thread_id` to tie follow-up queries to the same LangGraph checkpoint thread; when omitted, the runtime generates one per invocation.

These correlation fields support **observability** (trace ↔ response) and **external agent sessions** (same `thread_id` across related MCP or CLI calls). They are set in `run_query` (`src/graphs/core.py`) after the graph finishes, not by individual response builders in the supervisor.

There is no separate `DataRequest` model or `status` enum — outcome is conveyed through `results` plus natural-language `message`.

### Future work: re-adding core data addition

Public ingest (CLI `ingest`, MCP `submit_person_data`, `EntityQuery.provided_data`, enrich/validator loop) was removed June 2026. Planned return:

- Internal coordination via specialist agents (including seed/specialist persist paths).
- No restoration of the old single-step public `provided_data` handshake without a new design review.

Historical reference: tasks `2026-06-02-1000-redesign-ingestion-handshake` (introduced) and `2026-06-05-1000`–`1050` (removed from public surface).

---

## Technical Foundation

- **Primary Framework**: LangGraph (Python) with explicit stateful graphs
- **Checkpointer**: SQLite (`langgraph-checkpoint-sqlite`)
- **Integration**: MCP server for external AI agents (JSON-only)
- **Language & Standards**: Python 3.12+, strict typing with Pydantic, high code quality
- **Observability**: LangSmith tracing from day one; successful responses echo `trace_id` when tracing is on. See README.md for setup (create account + key, copy .env.example, set vars). The `get_langsmith_trace_url()` helper (in `src/utils/langsmith.py`) turns a `trace_id` into a clickable URL; it auto-resolves org/project scope from the LangSmith API when env UUIDs are unset, and is printed by the CLI after JSON output.

---

## Collaboration Model

- **Cursor**: Primary environment for implementation and heavy editing.
- **Grok Build**: Parallel partner for planning, architecture, review, and exploration.
- Preferred flow: Cursor does the majority of implementation. Grok is used for plans, architectural decisions, and reviews.

Work for Cursor is delivered through structured prompts in `prompts/cursor/next/`.

See `prompts/cursor/WORKFLOW.md` for the current handoff protocol.

---

## Working Principles

- **Scope discipline is mandatory.** Explicit scope boundaries in prompts must be respected. If out-of-scope work appears necessary, stop and escalate rather than proceeding.
- Prefer **simplification and deletion** over adding new abstractions.
- All changes should be **small and reviewable**.
- `docs/architecture.md` (this document) is the active source of truth for current implementation decisions.
- `prompts/system/CORE_PROMPT.md` is the stable source of truth for long-term principles and how we work.

---

## Current Phase Focus (as of June 2026)

The seed-data-context redesign is **implemented** (Cursor slices `2026-06-09-1500` through `1720` via the reprocess queue):

- Seed JSON origin (`<network_root>/seed.json`; example at `examples/networks/crm/`) with no legacy `id` in the file; public `results["id"]` = stable UUID
- No `core_data` specialist; `name`/`employer` are specialist-owned like any other attribute
- Supervisor is a pure planner (resolves seed, classifies, builds full context plan in state)
- Graph: `supervisor` → `build_context` → `invoke_specialists` → `assemble_response`
- Agent Factory template with 3 scenarios (`found` / `pending` / `N/A`), `specialist_contrib`, `id`/`context`/`target_fields`
- Canonical rename: `person_id` → `id` everywhere (slice 1300, June 2026)
- Full integration, docs refresh, specialist re-gens, removal of core-person-field privileges, and legacy `id` elimination complete

See `docs/plans/seed-data-context-architecture.md` and the reprocess reviews (`prompts/cursor/done/2026-06-09-*-reprocess/`).

**Phase 1 specialist research (implemented, sync):** On cache miss, specialists call `run_field_research` inline (LLM + Tavily `web_search`, bounded tool rounds). Low confidence → `na` + `reason`; API/timeout failure → `pending`. **Async dispatch** (non-blocking queries) is deferred — see `docs/plans/specialist-research-phase1.md`.

**Research prompt context (implemented, June 2026):** `build_research_prompts()` applies **MVR-driven bind disambiguation** (`MvrPolicy.bind_fields` from `network.json`) and includes **peer specialist findings** from `_research_context()` (other categories for the same `entity_id`). Templates: `src/agents/factory/templates/research/`. Follow-on hardening: `docs/plans/research-robustness-backlog.md`.

**Next phases:** async research dispatch (non-blocking queries), Tavily Extract/Crawl, research robustness items in backlog. Attribute-scoped `results` and specialist-first merge are already live (`2026-06-04-1400-filter-query-results-and-trace-url`).

See `TODO.md` for follow-ups.

---

**Last major update:** June 2026 (MVR redesign target protocol documented M1; Program 1 provenance complete; seed-data-context + sync specialist research)
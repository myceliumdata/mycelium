# Mycelium — Architecture & Current Direction

**Status:** Living document (as of June 2026)  
**Purpose:** Current architecture, key decisions, and implementation guidance for the active phase.

> **Note:** This document replaces the previous `docs/vision.md` and `docs/phase-1-direction.md`. The latter two are now considered historical.

### Architecture rationales (why)

This doc focuses on **what** and **how**. For **why** behind major decisions, see [`architecture/whys/`](architecture/whys/README.md) — short, linkable rationales you can read without losing the main narrative.

| Topic | Rationale |
|-------|-----------|
| Two-step query (`delivery_id`, attrs on step 1 only) | [two-step-query-protocol.md](architecture/whys/two-step-query-protocol.md) |
| Specialist-owned data (no `core_data`) | [specialist-owned-data.md](architecture/whys/specialist-owned-data.md) |
| Identity vs lookup vs MVR | [identity-lookup-and-mvr.md](architecture/whys/identity-lookup-and-mvr.md) |
| Three-layer storage (canonical, indexes, protocol record) | [three-layer-storage-model.md](architecture/whys/three-layer-storage-model.md) |
| Data factory (not MCP on raw data) | [data-factory-origin.md](architecture/whys/data-factory-origin.md) |
| Computation-centric provenance | [computation-centric-provenance.md](architecture/whys/computation-centric-provenance.md) |
| Warehouse factory stack (discovery → routing → execution) | [warehouse-factory-stack.md](architecture/whys/warehouse-factory-stack.md) |
| Metering economics (quotes, marginal pricing) | [metering-economics.md](architecture/whys/metering-economics.md) |
| Multi-record-type routing; fan team vs franchise | [multi-record-type-routing.md](architecture/whys/multi-record-type-routing.md) |
| Specialist class hierarchy (framework starting points) | [specialist-class-hierarchy.md](architecture/whys/specialist-class-hierarchy.md) |

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

The **CLI** (`query`) and **MCP** (`describe_network`, `query_entity`, `health_check`) expose **lookups only** via the **target two-step protocol** — step 1: `id` or `lookup`; step 2: `delivery_id` (+ `quote_id` when metered). No `provided_data` on the public model. **Why two steps:** [two-step-query-protocol.md](architecture/whys/two-step-query-protocol.md). Mechanics: [MVR redesign (target protocol)](#mvr-redesign-target-protocol). MCP **`describe_network`** returns author `guide.md`, ontology categories, framework policy, and usage examples.

Data addition via the public API was removed in the June 2026 refactor (tasks 1000–1050). It will return later as **internal agent coordination**, not as a direct caller-supplied payload.

### Seed bootstrap and identity (June 2026 — seed elimination)

- **Optional fixture:** `<network_root>/seed.json` — static `rows[]` array for bootstrap only (not read at query time). Committed CRM example: `examples/networks/crm-seeded/seed.json`. Import via `./bin/refresh-example-network crm-seeded` or `mycelium network create` when the file is present. See [seed-bootstrap.md](seed-bootstrap.md) for the three bootstrap patterns (None / JSON→MVR / custom handler).
- **Bootstrap phase:** `network.bootstrap.run_network_bootstrap(paths)` orchestrates create/refresh bootstrap — applies paths, MVR category merge, registry reset, loads `guide.md` into `BootstrapContext`, then invokes the handler declared in **`network.json` → `bootstrap`**. Every network declares **`module`** (Python module path) and **`handler`** (class name). Optional **`seed_record_type`** selects the record type for `DefaultSeedHandler` rows (else `mvr.default_record_type`). Framework handlers use modules under `network.*` (imported from the installed package); network-pack handlers use modules under `<network_root>/bootstrap_handlers/` (loaded via `sys.path`). CRM’s `DefaultSeedHandler` imports `seed.json` `rows[]` via `ensure_entity_bind_fields` (`source=seed_bootstrap`, `validation_state=validated`) using each row’s bootstrap record type `mvr.bind_fields`. `bootstrap_seed_at_paths()` is a thin wrapper returning `entities_committed`. Bootstrap bypasses the two-step lookup/create protocol by design; baseball uses a custom pack handler under `bootstrap_handlers/`.
- **Bootstrap manifest (required):**
  - **Framework handler (CRM):** `"module": "network.bootstrap.handlers.default_seed"`, `"handler": "DefaultSeedHandler"`.
  - **Network-pack handler (custom / baseball):** `"module": "bootstrap_handlers.<module>"`, `"handler": "<ClassName>"` — class must implement `run(self, ctx: BootstrapContext) -> BootstrapResult`. Pack modules live under `<network_root>/bootstrap_handlers/` and are copied from committed examples on refresh when present.
  - Handler-only manifests (e.g. `"handler": "default_seed"` without `module`) are rejected.
- **Stable test imports:** `network.seed_import` re-exports `import_seed_file`, `count_seed_rows`, and `bootstrap_seed_at_paths` for tests and legacy callers.
- **Transform (maintainers):** `examples/networks/crm-seeded/prepare_seed.py` builds example `seed.json` from a CRM source file (name + employer only; no legacy `id` in the file). Full prototype data: git tag `prototype`.
- **Runtime store:** Per-record-type entity files at `<network_root>/entities/<record_type>.json`. Each file holds uuid4 ids, `bind_values` keyed by that record type's `mvr.record_types.<name>.bind_fields`, generic `bind_index`, and per-field indexes. `ensure_entity_bind_fields` assigns stable ids on import; step-1 resolve infers record type from lookup key shape — see [query-record-type-router.md](query-record-type-router.md). Seed `rows[]` import into the bootstrap record type (`bootstrap.seed_record_type` or `mvr.default_record_type`) on refresh or `network create`.
- **No `core_data` specialist** — MVR bind fields come from the registry; specialists may override them later when requested (CRM example: `name`, `employer`).

### Supervisor and graph (current)

The **supervisor** (`src/agents/supervisor.py`) resolves registry matches, classifies `requested_attributes`, and plans which generated specialists to invoke. It does **not** build the final response when specialists are needed.

**Graph flow** (`src/graphs/core.py`):

```
START → target_resolve → supervisor → validate_entity → metering_gate → build_context → invoke_specialists → assemble_response → END
              └──────────────────────── assemble_response (step-1 lookup_resolved / quote_required / not_found)
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

Generated specialists (`src/agents/specialists/*_specialist.py`, Agent Factory template) implement three scenarios: has data, **synchronous** field research on cache miss (when `OPENAI_API_KEY` and the active web search key are set), or pending / N/A. Research runs via `tools.research.run_field_research` and pluggable `web_search` (`src/tools/web_search.py`; default provider **Tavily** via `SEARCH_PROVIDER=tavily`). `tools.tavily` remains a backward-compat re-export. See `docs/plans/seed-data-context-architecture.md`, `docs/plans/specialist-research-phase1.md`, and Cursor slices `2026-06-09-1100`–`1400`.

Pre–registry ingest (`enrich`, `validator`, `person_prep`) and the SQLite `people` table were removed June 2026. See [`docs/legacy-ingest-and-storage-reference.md`](legacy-ingest-and-storage-reference.md).

---

## Current Data Model (Phase 1 — Strictly Minimal Core)

The core `IdentityRecord` aligns with registry `bind_values`:

```python
class IdentityRecord(BaseModel):
    id: str = ""
    bind_values: dict[str, str] = Field(default_factory=dict)
```

**Identity rules:**
- Bootstrap seed rows supply values for the active record type's `mvr.bind_fields`; runtime and public `results["id"]` use the stable UUID from the entity store (assigned on import via `ensure_entity_bind_fields`).
- MVR bind fields are specialist-owned like any other attribute when requested (no privileged core filter).
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

- **Entities (queries):** per-record-type stores at `<network_root>/entities/<record_type>.json` via `EntityRegistry` (public API unchanged). **`EntityStore`** (`src/storage/entity_store.py`) handles persistence: default **`entities_document_v1`** JSON, optional **`minisql_v1`** SQLite at `entities/<record_type>.sqlite` when `entity_count()` crosses threshold (env `MYCELIUM_ENTITY_OPTIMIZE_STORAGE_THRESHOLD`, default 50). JSON backup: `entities/<record_type>.json.pre-minisql-v1`. Network bootstrap defers entity flushes (`bootstrap_deferred_save`) — one disk write per record type at handler end. **Deferred:** moving registry ownership to an identity agent per record type after the full baseball example ships.
- **Specialists (opaque):** per-category data under `<network_root>/agents/<category>/`, owned and laid out by specialist code (`SpecialistStorage` in `src/agents/specialists/base.py` — **specialists package only**). Internally, CRM specialists use **`versioned_provenance_v1`** (`versions[]` + `current_version_id`). Framework code **must not** read or write those files directly; it dispatches through `agents.specialists.protocol` (tag `specialist_isolation`, June 2026).
- **Framework write path:** `agents/attribute_write.py` resolves taxonomy owners, calls specialist dispatch (`write_fields` / multi-category bind), then syncs `entities.json` cache and indexes from returned current values. Seed import, create-on-deliver, and research persist use the same dispatch boundary.
- **Framework read path:** context, provenance, admin status, and `tools/research` consume **normalized snapshots** from dispatch (`FieldSnapshot`, `FieldContextSnapshot` in `src/agents/specialists/snapshots.py`) — not raw `versions[]` layout. See § Specialist I/O protocol below.
- **SQLite:** `<network_root>/checkpoints.sqlite` (LangGraph checkpointer). Optional `<network_root>/mycelium.db` — empty bootstrap file only; no identity tables.

See `src/storage/core.py` (path bootstrap for MCP/admin startup).

---

## Specialist I/O protocol (June 2026)

**Component isolation:** storage layout and versioned field mechanics stay inside `src/agents/specialists/`. Cross-boundary traffic uses dispatch + published snapshot shapes (protocol v1).

| Dispatch entry | Role |
|----------------|------|
| `dispatch_write_fields` / `dispatch_write_bind_fields_multi` | Bind and attribute writes |
| `dispatch_read_fields` | Single-entity reads; `include_versions=True` → `provenance` on snapshot |
| `dispatch_read_category_slice` | Graph context slices (extended attrs) |
| `dispatch_bootstrap_entity` | Seed/bootstrap materialization |
| Research handlers | `dispatch_mark_pending`, `dispatch_persist_research`, `dispatch_append_research_audit` |

**`FieldSnapshot`** (per field from `read_fields`):

- `value`, `status` (`found` \| `na` \| `pending` \| `empty`), `updated_at`
- `provenance` (optional): `{ current_version_id, versions[] }` for API/admin — framework passes through; does not parse internal storage

**`FieldContextSnapshot`** (per field in graph/research context):

- `value`, `status`, `sources[]`, `updated_at`
- `operator`: `{ set, value, at, note }` for research deference

Early CRM specialists subclass **`SpecialistAgent`** (`src/agents/specialists/agent.py`) and expose a module singleton `AGENT`; graph entrypoints delegate to `AGENT.run(state)` and protocol dispatch resolves `get_agent_instance(name)` → `AGENT.write_fields` / `read_fields` / etc. Users override storage or research by subclassing and replacing `AGENT`. Shared JSON mechanics live in the base class; `handlers.py` is an internal specialists-package helper only — framework code routes through `agents.specialists.protocol`, not `handlers` directly. Heterogeneous specialists (e.g. baseball warehouse) may use different internal storage if read/write handlers emit the same snapshots.

**Specialist hierarchy (June 2026 — in progress):** `SpecialistAgent` is the **framework root** (storage + protocol I/O), not a leaf. Example networks should subclass **middle tiers** in `src/agents/specialists/` — warehouse stat bases, product-team bases, research template — and keep pack modules thin. Baseball proved warehouse + derive patterns; M14 promotes `WarehousePlayerStatSpecialist` / `WarehouseTeamStatSpecialist` into the framework. Rationale and target tree: [specialist-class-hierarchy.md](architecture/whys/specialist-class-hierarchy.md).

**Storage migration policy (June 2026):** Base `SpecialistAgent.optimize_storage()` returns `True` when `current_strategy()` is `versioned_provenance_v1` and `record_count()` ≥ threshold (default **50**, env `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD`). Each category’s `AGENT` evaluates independently. Subclasses may override `optimize_storage_threshold()` or `optimize_storage()` (e.g. opt-out). Crossing threshold calls `migrate_to("minisql_v1")` before writes.

**`minisql_v1` storage (June 2026):** Shared module `src/storage/minisql_v1.py` backs both specialist category stores (`<agents>/<category>/storage.sqlite`) and per-record-type entity stores (`entities/<record_type>.sqlite` via `EntityStore`). When a specialist crosses threshold, `SpecialistStorage.migrate_to("minisql_v1")` copies `storage.json` into SQLite, renames JSON to `storage.json.pre-minisql-v1`, and updates `storage_strategy.json`.

**Specialist hot path (incremental, June 2026):** `write_fields` / `read_fields` on `minisql_v1` use **per-entity** `load_entity` + `save_entity` — one `entity_id` per bind, not a full-table rewrite. Each upsert runs `DELETE FROM field_records WHERE entity_id = ?` then re-inserts **every field row currently in that entity's in-memory record** (typically 1–2 bind fields at bootstrap; more after research). That is **entity-scoped** replace, not single-`(entity_id, field_name)` patch: cost per write is O(fields on that entity), not O(all entities in the category). Bulk `load()` / `save()` / `save_payload` (full table replace) remain for migration, tests, and `analyze_storage`. Entity registry bulk flush semantics are unchanged (deferred bootstrap save; `save_entities_document` still replaces the full document per record type when not deferred). Protocol snapshots and CRM behavior under threshold are unchanged.

---

## Networks (product model — documented June 2026; runtime in Phases 2–4)

Users download the **framework** (this repo: `src/`, `bin/`, docs, tests) and run **named networks** at user-chosen **`network_root`** paths. Network data never has to live inside the clone; it can be on Dropbox, another disk, etc.

| Layer | Location | Notes |
|-------|----------|-------|
| **Framework** | Repo clone | Code, tooling, tests |
| **Network root** | User-chosen directory | All runtime artifacts for one network |
| **Example network** | `examples/networks/` (Phase 4) | Committed reference (e.g. CRM) |
| **Live CRM** | User path (e.g. `~/mycelium-networks/crm-seeded`) | Bootstrap via `./bin/refresh-example-network crm-seeded` |

**Standard layout under `network_root`** (target contract):

```
<network_root>/
  network.json          # manifest; bootstrap.module + bootstrap.handler (class) required
  guide.md              # network policy prose (bootstrap context + MCP describe_network)
  seed.json             # optional bootstrap fixture (DefaultSeedHandler reads at refresh/create)
  bootstrap_handlers/   # optional network-pack bootstrap modules (copied from examples)
  entities/             # per-record-type runtime stores (e.g. person.json)
  categories.json       # skeleton ontology at create; runtime (see docs/examples/sample-categories.json)
  agent_registry.json
  deliveries.json       # runtime — step-1 delivery scopes (TTL; MYCELIUM_DELIVERIES_PATH)
  quotes.json           # runtime — metered quotes (TTL; MYCELIUM_QUOTES_PATH)
  entitlements.json     # runtime — metering entitlements (when enabled)
  credits.json          # runtime — metering credits (when enabled)
  specialists/          # generated *_specialist.py (Phase 5; per-network)
  agents/<category>/storage.json
  checkpoints.sqlite
  mycelium.db          # optional empty bootstrap file (no identity tables)
```

**Ontology vs classification:** `network create` writes a **skeleton ontology** (categories, specialists, minimal `attribute_map` from examples). The classification engine still **grows `attribute_map` lazily** at query time when clients request attributes not yet mapped.

**Selection (target resolution order):** CLI `--network-dir` → CLI `--network` (name via registry, Phase 3) → env `MYCELIUM_NETWORK_ROOT` → env `MYCELIUM_NETWORK` → **default network** from user config (Phase 3). Unconfigured installs raise a clear error pointing to `./bin/refresh-example-network crm-seeded`.

**MCP:** One long-lived stdio process **per network**. Run several MCP servers in parallel by giving each client entry a different `MYCELIUM_NETWORK_ROOT` while `cwd` stays the framework repo. `refresh_runtime_from_disk()` reloads only that process’s network files. No network switching inside a single MCP process.

**Terminology:** Product **network** ≠ LangGraph **agent collective** ≠ social **profiles** (attribute domain). Full map and phased delivery: [`docs/plans/networks-terminology.md`](plans/networks-terminology.md). Pre-networks baseline: git tag `prototype`.

### Framework credentials vs network data (June 2026)

**API keys and provider config are framework-level, not per-network.** One `.env` (or equivalent env block in the MCP client) per machine/operator covers all networks:

| Lives in framework `.env` (process-wide) | Lives under `network_root` (per network) |
|------------------------------------------|------------------------------------------|
| `OPENAI_API_KEY`, `SEARCH_PROVIDER` (`tavily` default), active search key (`TAVILY_API_KEY` / `EXA_API_KEY` / `BRAVE_SEARCH_API_KEY`), `ANTHROPIC_API_KEY`, … | `seed.json`, `categories.json`, `agent_registry.json`, `specialists/`, `agents/` |
| `LANGCHAIN_*`, `LANGSMITH_*` (tracing) | `checkpoints.sqlite`, `mycelium.db`, `network.json` |
| `MYCELIUM_RESEARCH_*` tuning, `MYCELIUM_*_MODEL` (LLM model per subsystem — see `.env.example`; computation codegen recommends `gpt-4o+`) | — |

CLI and MCP call `load_dotenv()` at startup from the **framework** working directory. **`MYCELIUM_NETWORK_ROOT`** / **`MYCELIUM_NETWORK`** select which data directory to use; they do not hold secrets. LLM model selection is env-only via `MYCELIUM_*_MODEL` variables (see `.env.example`); computation codegen production use recommends `MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o` or stronger. Launching or registering a network does **not** copy or create a `.env` inside `network_root`.

**MCP:** `cwd` = framework repo; per-server `env` sets only network selection (plus the same shared API keys as other servers on that host). **`query_entity`** uses the target protocol: step 1 `id` or `lookup`, step 2 `delivery_id` — see [MVR redesign (target)](#mvr-redesign-target-protocol) below.

Future (not v1): per-network LangSmith project names, optional credential profiles — see `TODO.md`.

---

## MVR redesign (target protocol)

**Status:** Shipped (M1–M10, June 2026) — target two-step protocol on all public surfaces.  
**Program:** [`docs/plans/mvr-redesign-program.md`](plans/mvr-redesign-program.md) · **Operator guide:** [`docs/plans/mvr-best-practices.md`](plans/mvr-best-practices.md) · **Examples:** [`docs/plans/mvr-redesign-entity-query-examples.md`](plans/mvr-redesign-entity-query-examples.md)

**M3 (models):** `EntityQuery` and `QueryResponse` accept target fields with Pydantic step-1/step-2 validation.

**M4 (resolve):** Per-field inverted indexes on registry MVR bind fields; graph `target_resolve` node returns `lookup_resolved` + `delivery_id` for step-1 `id`/`lookup`.

**M5 (deliver):** Step-2 `delivery_id` loads `DeliveryScope` and returns `found` / `assembled` with registry `results[]`; attrs/provenance from step-1 scope hydrate internal graph state.

**M6 (metering):** Metered step-1 with attrs → `quote_required` + `delivery_id`; step-2 requires `quote_id` when `metering.enabled`; batch line items scale × N entities.

**M7 (create):** Full MVR lookup + attrs on 0 matches → create-on-deliver scope; step-2 `bind_provisional_from_scope` + research.

**M8 (batch):** N-match scopes research and deliver all entities; batch `provenance.entities[]`.

**M9 (public surfaces):** CLI, MCP, admin API migrated to target protocol; legacy `entity_key` / `binding` removed from public entry points.

**M10 (polish):** Admin UI two-step form; backlog tests; Program 3 removed legacy graph path and env flag.

**Active — Program 2** (MVR in specialist storage, unified write): [`attribute-provenance-program2.md`](plans/attribute-provenance-program2.md). **Complete** (Slices 1–3 shipped).

### Three separated concerns

| Concern | Meaning |
|---------|---------|
| **Identity** | Stable **`id` (UUID)** only — no name string as primary key |
| **Lookup** | Find candidate rows by **partial field match** (AND within `lookup`) |
| **MVR** | Per-network **minimum field set** to **create** a new entity and **run extended research** |

Previously conflated in `entity_key`, `binding`, and `mvr.name_source` — all removed from the public protocol (June 2026).

### Two-step delivery (like quotes)

**Rationale:** [two-step-query-protocol.md](architecture/whys/two-step-query-protocol.md)

1. **Step 1 — Resolve:** send `id` **or** `lookup` (AND within map); optional `requested_attributes` and `provenance` **on this step only**. Response: `total_matches`, empty `results[]`, and `delivery.delivery_id` (`delivery.create_on_deliver: true` only when step 2 will create from full MVR with 0 registry hits; omitted otherwise) (+ `quote` when `metering.enabled`).
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

Legacy outcomes (`entity_unknown`, `entity_key_unresolved`, `entity_bound_provisional`, …) are retired — removed in Program 3 (June 2026).

### Create flow (0 matches) — M7

Partial `lookup` with 0 matches → `not_found` (no create). Full MVR in step-1 `lookup` with 0 registry matches → step-1 returns `lookup_resolved` with `total_matches=0`, `delivery.create_on_deliver: true`, and a `delivery_id` scoped for provisional create; step-2 deliver calls `bind_provisional_from_scope` from scope `lookup` then runs attribute research when attrs were bound on step 1. `requested_attributes` are optional for identity-only create (no research on step 2 unless attrs were requested). Each MVR bind field is supplied in `lookup` like any other key in the map.

**Step-1 `message` (aligned with JSON):** existing match — e.g. `1 registry match. Use delivery_id on step 2 to deliver.`; create pending — `No registry match. Full MVR lookup — step 2 will create a provisional entity, then deliver.`

### Batch deliver (N entities) — M8

Multi-match step-1 scopes carry `entity_ids[]` (N > 1). Step-2 deliver hydrates all N rows, invokes specialists **per entity** (no silent truncation), and returns N `results[]` entries with requested attrs merged per row. When step-1 bound `provenance=true`, step-2 `assembled`/`found` responses attach `provenance.entities[]` with one entry per delivered id (extended attrs only). Create-on-deliver remains N=1 (`create_on_deliver` scopes never batch).

### Public surfaces (CLI, MCP, admin) — M9

CLI `query`, MCP `query_entity`, and admin `POST /query` use the **target protocol only** — no `entity_key` / `binding` on public entry points. Public JSON uses `QueryResponse.public_dict()` / `public_json()` — omits fields that do not apply to the response `outcome` (e.g. step-2 `found` omits `total_matches` and `delivery`; empty `required_fields`/`suggestions` and null `quote`/`provenance`/`trace_id` are absent keys; `delivery.create_on_deliver` only when true). Step-1 adds `lookup_incomplete` (partial lookup missing MVR fields) and `lookup_suggested` (bind-field conflict or fuzzy near-miss); `lookup_suggested` retry hints use `suggestions[].suggested_lookup` (partial/full MVR bind map) and optional `suggestions[].id`; `confirm_new_entity` on step-1 lookup opts into create after suggestions. Example query JSON under `examples/networks/*/queries/` documents two-step resolve → deliver. Admin UI (`admin-ui/`) uses lookup fields + stored `delivery_id` (M10); shows `total_matches: 0 (full MVR)` when `create_on_deliver` is true.

**Status inspect (D2-b):** CLI `mycelium network status --id` / `--lookup-json` and admin `GET /status?id=` / `?lookup=` accept exact `id` or `lookup` only (no fuzzy suggestions). JSON responses include `resolve: { id, lookup }` mirroring the inspect input, plus `resolve_matches`, `resolve_kind`, and `entity_fields[]` with versioned storage detail.

### Operator notes — M10

- `delivery_id` and `quote_id` expire after **5 minutes** by default (`MYCELIUM_DELIVERY_TTL_SEC`, `MYCELIUM_QUOTE_TTL_SEC`). Abandoned quotes leave orphan delivery scopes until TTL — safe to ignore.
- Batch step-2 deliver invokes specialists **sequentially** per entity (N×M); parallelize only if profiling requires it.

### Indexes (target)

One inverted index per MVR field on `entities.json` (normalized value → `[uuid, …]`). Compound indexes deferred (Program 2 / operator).

---

## Public query flow (current runtime)

Registry rows hold `id` and `bind_values` keyed by active record type `mvr.bind_fields` (CRM example: `name`, `employer`; baseball player record type: `player`, `debut_team`, `debut_year`). Public `results[]` flatten those bind keys alongside `id`. Callers send a query-only **`EntityQuery`** using the [target two-step protocol](#mvr-redesign-target-protocol). The graph state always includes `MyceliumGraphState.query`; LangSmith trace input therefore always shows a `query` section even for internal-only operations.

### Flow summary

| Intent | What the caller sends | Graph path | What comes back |
|--------|----------------------|------------|-----------------|
| **Resolve (step 1)** | `id` or `lookup`; optional `requested_attributes`, `provenance` | `target_resolve` → `assemble_response` | `lookup_resolved` or `quote_required`; `total_matches`; `delivery.delivery_id`; empty `results[]` |
| **Deliver identity (step 2)** | `delivery_id` (+ `quote_id` when metered) | `target_resolve` → `supervisor` → … → `assemble_response` | `found`; full identity `results[]` |
| **Deliver with attrs (step 2)** | `delivery_id` (+ `quote_id` when metered); attrs bound on step 1 | `target_resolve` → `supervisor` → `build_context` → `invoke_specialists` → `assemble_response` | `assembled`; `results[]` with requested attrs merged per row |
| **Miss / invalid** | bad `id`, partial lookup with 0 matches (not full MVR), expired tokens | `target_resolve` → `assemble_response` | `not_found` |
| **Create pending (step 1)** | full MVR `lookup`, 0 registry matches | `target_resolve` → `assemble_response` | `lookup_resolved`; `total_matches=0`; `delivery.create_on_deliver: true` |

### Response fields (query outcomes)

All external responses use the minimalist **`QueryResponse`** (`results`, `message`, `provenance`, `debug`, `trace_id`, `thread_id`):

- **`results`** — One dict per match. Always includes `"id"` (stable UUID). With no `requested_attributes`: `id` plus active MVR `bind_fields`. With `requested_attributes`: `id` plus only those keys after specialist-first merge (specialist value wins; seed provisional while pending). No `person_id` field.
- **`message`** — Primary channel: found / not-found / per-attribute status. Visiting agents read natural-language sentences built from supervisor classifications: **researching** (in-scope, pending), **unavailable** (researched, no value), **out_of_scope** (`category == "unknown"` — never "researching" wording). Found attribute values appear only in `results`, not repeated in `message`. Multi-match uses a collective prefix (`Found N records for 'key'.`).
- **`provenance`** — Optional structured version history. **`EntityQuery.provenance`** (request flag, default `false`) controls whether this block is populated; it is unrelated to the response field name. When `true` and the outcome delivers results (`assembled` / `found`) with requested extended attributes, `provenance.entities[]` lists each match `id` and per-attribute `current_version_id` + `versions[]` copied from specialist storage (MVR bind fields omitted). Default flat `results[]` is unchanged. Metering may charge a `query_provenance` line when enabled. See [`attribute-provenance-program1.md`](plans/attribute-provenance-program1.md).
- **`debug`** — Internal context (`lookup` / `delivery_id`, `requested_attributes`, outcome tags). Callers should not depend on it.
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

- Seed JSON origin (`<network_root>/seed.json`; example at `examples/networks/crm-seeded/`) with no legacy `id` in the file; public `results["id"]` = stable UUID
- No `core_data` specialist; MVR bind fields are specialist-owned like any other attribute when requested
- **Framework MVR generic vocabulary (June 2026):** `IdentityRecord.bind_values`, `LookupSuggestion.suggested_lookup` only, validation/context/suggestions driven by active `mvr.bind_fields` — no hardcoded CRM field pairs in `src/`. CRM example network unchanged (`name` + `employer` in seed and `results[]` because that is what CRM `network.json` declares). Verification: `./bin/smoke-crm-seeded-e2e`.
- Supervisor is a pure planner (resolves seed, classifies, builds full context plan in state)
- Graph: `target_resolve` → (`assemble_response` on step 1, or `supervisor` → `build_context` → `invoke_specialists` → `assemble_response` on step 2)
- Agent Factory template with 3 scenarios (`found` / `pending` / `N/A`), `specialist_contrib`, `id`/`context`/`target_fields`
- Canonical rename: `person_id` → `id` everywhere (slice 1300, June 2026)
- Full integration, docs refresh, specialist re-gens, removal of core-person-field privileges, and legacy `id` elimination complete

See `docs/plans/seed-data-context-architecture.md` and the reprocess reviews (`prompts/cursor/done/2026-06-09-*-reprocess/`).

**Phase 1 specialist research (implemented, sync):** On cache miss, specialists call `run_field_research` inline (LLM + `web_search` tool, bounded tool rounds). Backend is selected with `SEARCH_PROVIDER` (`tavily` default, or `exa` / `brave`). Low confidence → `na` + `reason`; API/timeout failure → `pending`. **Async dispatch** (non-blocking queries) is deferred — see `docs/plans/specialist-research-phase1.md`.

**Research prompt context (implemented, June 2026):** `build_research_prompts()` applies **MVR-driven bind disambiguation** (`MvrPolicy.bind_fields` from `network.json`) and includes **peer specialist findings** from `_research_context()` (other categories for the same `entity_id`). Templates: `src/agents/factory/templates/research/`. Follow-on hardening: `docs/plans/research-robustness-backlog.md`.

**Next phases:**

See `TODO.md` for follow-ups.

---

**Last major update:** June 2026 (framework MVR generic vocabulary; specialist isolation dispatch protocol)
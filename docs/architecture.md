# Mycelium — Architecture & Current Direction

**Status:** Living document (as of June 2026)  
**Purpose:** Current architecture, key decisions, and implementation guidance for the active phase.

> **Note:** This document replaces the previous `docs/vision.md` and `docs/phase-1-direction.md`. The latter two are now considered historical.

---

## Overview

Mycelium is an AI-native data management system in which intelligent agents autonomously organize, evolve, and maintain data sources.

The system uses networks of LangGraph agents to handle ingestion, schema evolution, validation, indexing, and continuous self-improvement — creating living, self-organizing information ecosystems.

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

The **CLI** (`query`, `seed`) and **MCP** (`query_person`, `list_specialist_routing`) expose **lookups only**. `PersonQuery` has `person_key` and optional `requested_attributes` — no `provided_data` on the public model.

Data addition via the public API was removed in the June 2026 refactor (tasks 1000–1050). It will return later as **internal agent coordination**, not as a direct caller-supplied payload.

### Seed origin and identity (June 2026 — seed-data-context redesign)

- **Canonical seed:** `data/seed.json` — static JSON origin of person records (`people` array). Replace the file manually to reset origin data; `bin/reset-mycelium` does **not** touch it.
- **Transform:** `data/prepare_seed.py` builds `seed.json` from `seed_crm.json` (name + employer only; no legacy `id` in the file).
- **Loader:** `src/agents/seed.py` assigns stable `person_id` (uuid5 from name|employer) at load time; public `results["id"]` is that UUID; supervisor resolves lookups via `find_by_key` (name or `person_id`).
- **No `core_data` specialist** — identity fields (name, employer) come from seed; specialists may override them later.

### Supervisor and graph (current)

The **supervisor** (`src/agents/supervisor.py`) resolves seed matches, classifies `requested_attributes`, and plans which generated specialists to invoke. It does **not** build the final response when specialists are needed.

**Graph flow** (`src/graphs/core.py`):

```
START → supervisor → build_context → invoke_specialists → assemble_response → END
              └──────────────── assemble_response (name-only / not found)
```

- **build_context** (`src/agents/context.py`) — union of seed + all specialist storage for the `person_id`(s).
- **invoke_specialists** — each required specialist receives full `context`, `current_person_id`, and `target_fields` (owned attributes only).
- **assemble_response** — unified `PersonResponse` from seed identity + specialist contributions.

Generated specialists (`src/agents/specialists/*_specialist.py`, Agent Factory template) implement three scenarios: has data, pending research (background stub thread), or N/A. See `docs/plans/seed-data-context-architecture.md` and Cursor slices `2026-06-09-15xx`.

Legacy **enrich**, **validator**, **person_prep**, and **core_identity** remain on disk as unwired legacy; queries do not depend on them.

---

## Current Data Model (Phase 1 — Strictly Minimal Core)

The core `Person` record is deliberately tiny:

```python
class Person(BaseModel):
    id: str
    name: str
    employer: str | None = None
```

**Identity rules:**
- Seed provides `name`, `employer` (no legacy `id`); public `results["id"]` and `person_id` are the stable UUID assigned by the seed loader (`agents/seed.py`).
- `name` and `employer` are specialist-owned like any other attribute when requested (no privileged core filter).
- There is no `extra` field on `Person`.

---

## Derivative / Non-Core Data

Phase 1 adds a **Classification Engine** (cached lookup in `src/agents/classification/`, backed by `data/categories.json`) that the supervisor uses for non-core `requested_attributes`. Known attributes are instant map lookups; first-time unknowns may call the LLM once (lazy, structured proposals), then cache—including garbage rejected as `unknown`. Batch tree evolution uses `CategoryTree.refresh_from_llm` (admin/off-path). Metadata flows to `audit_log`, `state.classifications`, and `response.debug` (see `docs/plans/classification-engine-phase1.md`).

**Phase 2 Agent Factory** adds on-demand creation of committed specialist agents (Jinja2 template in `src/agents/factory/`, `data/agent_registry.json`, `src/agents/specialists/*.py` with an AUTO-GENERATED header, and `specialist_dispatcher`). The supervisor triggers `AgentFactory.create_specialist` when classification names an `assigned_agent` that is not yet registered. Each specialist starts with per-category flat JSON plus `storage_strategy.json` hooks for future self-evolution (see `docs/plans/agent-factory-phase2.md`).

- We **explicitly do not pre-define** derivative attributes, dataset types, or storage structures.
- The supervisor classifies requested attributes (lookup only in Phase 1) before routing; real specialist handoff is future work.
- If no suitable agent exists, the system should support creating one.
- How a specialist agent stores and manages its data is not defined centrally.

**Phase 1 Practical Rule:**
- Do not create shared tables or infrastructure for "derivative datasets" in the core storage layer.
- When the supervisor sees non-core attributes, it notes this in the response and audit log rather than creating formal derivative records.

---

## Storage (current)

- **Seed (queries):** `data/seed.json` via `agents.seed` — not auto-loaded into SQLite on query.
- **Specialists:** per-category JSON under `data/agents/<category>/` (`SpecialistStorage` in `src/agents/specialists/base.py`), keyed by `person_id`.
- **SQLite:** `data/mycelium.db` (legacy `people` table; checkpoints/history only in this phase) and `data/checkpoints.sqlite` (LangGraph checkpointer).

See `src/storage/core.py` (DB retained for checkpointer-era compatibility; people auto-seed disabled by default).

---

## Public query flow (current)

Core storage holds only `id`, `name`, and `employer`. Callers send a query-only **`PersonQuery`** (`person_key`, optional `requested_attributes`). The graph state always includes `MyceliumGraphState.query`; LangSmith trace input therefore always shows a `query` section even for internal-only operations.

### Flow summary

| Intent | What the caller sends | Graph path (current / target) | What comes back |
|--------|----------------------|-------------------------------|-----------------|
| **Lookup (found)** | `person_key` only | `supervisor` → `assemble_response` (seed) | `results`: identity dict(s) from seed; `message`: "Found record for …" |
| **Lookup (miss)** | unknown `person_key` | `supervisor` → `assemble_response` | `results`: `[]`; not-found `message` |
| **Non-core attrs** | `person_key` + attrs | `supervisor` → `build_context` → `invoke_specialists` → `assemble_response` | `results`: seed identity; `message`: specialist status (pending / N/A / values) |

### Response fields (query outcomes)

All external responses use the minimalist **`PersonResponse`** (`results`, `message`, `debug`, `trace_id`, `thread_id`):

- **`results`** — Identity records from seed (name, employer); `"id"` and `"person_id"` are the stable UUID from the seed loader (disambiguation for multi-result sets; specialist storage key). Specialist overrides may apply later.
- **`message`** — Primary channel: found / not-found / specialist attribute status (no "core record" wording).
- **`debug`** — Internal context (original `person_key`, `requested_attributes`, outcome tags). Callers should not depend on it.
- **`trace_id`** — LangSmith trace identifier for this graph invocation when `LANGCHAIN_TRACING_V2` is enabled; otherwise `null`. Lets operators and developers jump from a JSON response to the matching trace in LangSmith for debugging. When creating your LangSmith API key, select **Personal Access Token (PAT)** (prefix `lsv2_pt_`). `LANGCHAIN_PROJECT` (default "mycelium") names the tracing project in the LangSmith UI — it will be created automatically on first use; no manual pre-creation required. See README.md for full setup steps.
- **`thread_id`** — Conversation/session identifier for this request. CLI and MCP callers may pass a stable `thread_id` to tie follow-up queries to the same LangGraph checkpoint thread; when omitted, the runtime generates one per invocation.

These correlation fields support **observability** (trace ↔ response) and **external agent sessions** (same `thread_id` across related MCP or CLI calls). They are set in `run_query` (`src/graphs/core.py`) after the graph finishes, not by individual response builders in the supervisor.

There is no separate `DataRequest` model or `status` enum — outcome is conveyed through `results` plus natural-language `message`.

### Future work: re-adding core data addition

Public ingest (CLI `ingest`, MCP `submit_person_data`, `PersonQuery.provided_data`, enrich/validator loop) was removed June 2026. Planned return:

- Internal coordination via specialist agents (including seed/specialist persist paths).
- No restoration of the old single-step public `provided_data` handshake without a new design review.

Historical reference: tasks `2026-06-02-1000-redesign-ingestion-handshake` (introduced) and `2026-06-05-1000`–`1050` (removed from public surface).

---

## Technical Foundation

- **Primary Framework**: LangGraph (Python) with explicit stateful graphs
- **Checkpointer**: SQLite (`langgraph-checkpoint-sqlite`)
- **Integration**: MCP server for external AI agents (JSON-only)
- **Language & Standards**: Python 3.12+, strict typing with Pydantic, high code quality
- **Observability**: LangSmith tracing from day one; successful responses echo `trace_id` when tracing is on. See README.md for setup (create account + key, copy .env.example, set vars). The optional `get_langsmith_trace_url()` helper (in `src/utils/langsmith.py`) turns a `trace_id` into a clickable URL; it is exercised in the CLI output.

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

- Seed JSON origin (`data/seed.json` + `data/prepare_seed.py`) with no legacy `id`; public `results["id"]` = stable `person_id` (UUID)
- No `core_data` specialist; `name`/`employer` are specialist-owned like any other attribute
- Supervisor is a pure planner (resolves seed, classifies, builds full context plan in state)
- Graph: `supervisor` → `build_context` → `invoke_specialists` → `assemble_response`
- Agent Factory template with 3 scenarios (`found` / `pending` / `N/A`), `specialist_contrib`, `person_id`/`context`/`target_fields`
- Full integration, docs refresh, specialist re-gens, removal of core-person-field privileges, and legacy `id` elimination complete

See `docs/plans/seed-data-context-architecture.md` and the reprocess reviews (`prompts/cursor/done/2026-06-09-*-reprocess/`).

**Next phases:** robust pending handling, peer context retrieval, real LLM+tools research, richer output shape.

See `TODO.md` for follow-ups.

---

**Last major update:** June 2026 (seed-data-context redesign integrated)
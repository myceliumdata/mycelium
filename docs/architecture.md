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

### Supervisor as coordinator (Phase 1 complete)

The **supervisor node** (`src/agents/supervisor.py`) is a thin coordinator and router:

- It evaluates the inbound `PersonQuery` (`person_key` + optional `requested_attributes`) and emits a `route` decision plus audit log. For the current public query-only surface it always routes to the core specialist (`route="core_data"`).
- Classification, core lookup via `CoreIdentity`, and construction of the minimal `PersonResponse` (`results`, `message`, `debug`, `trace_id`, `thread_id`) are performed by the specialist.
- **Core data specialist** — `src/agents/core_data.py` defines `core_data_agent`, the LangGraph node that owns core CRM lookups (`find_by_key` via `CoreIdentity`). Wiring supervisor → `core_data_agent` (with the conditional edge in `graphs/core.py`) was completed in tasks 1070/1100 and the final alignment pass was 1110.
- **CoreIdentity** — `src/agents/core_identity.py` is the storage facade used by `core_data_agent` (and available for future specialists).

Legacy **enrich**, **validator**, and **person_prep** modules remain on disk as *unwired legacy* (see the module docstrings in those files). They are not imported by `src/agents/__init__.py` and are not present in the compiled public graph. They are reserved exclusively for future internal agent-coordinated data addition (see TODO.md "Re-adding data addition").

Full specialist-agent routing for non-core attributes is still future work. When a query requests non-core attributes, the core record (if present) is returned and the `message` field contains a narrative (e.g. "we're still researching X").

---

## Current Data Model (Phase 1 — Strictly Minimal Core)

The core `Person` record is deliberately tiny:

```python
class Person(BaseModel):
    id: str
    name: str
    employer: str | None = None
```

**Core Rules:**
- `CORE_PERSON_FIELDS = {"id", "name", "employer"}`
- `MINIMUM_VIABLE_FIELDS = ["name", "employer"]`
- All other attributes (email, phone, demographics, social handles, etc.) are non-core and routed to specialist agents.
- There is no `extra` field on the core `Person` model.

The `Person` model represents only records in the primary core `people` table.

---

## Derivative / Non-Core Data

- We **explicitly do not pre-define** derivative attributes, dataset types, or storage structures.
- The supervisor classifies requested data and hands it off to the appropriate specialist agent.
- If no suitable agent exists, the system should support creating one.
- How a specialist agent stores and manages its data is not defined centrally.

**Phase 1 Practical Rule:**
- Do not create shared tables or infrastructure for "derivative datasets" in the core storage layer.
- When the supervisor sees non-core attributes, it notes this in the response and audit log rather than creating formal derivative records.

---

## Storage Constraints (Phase 1)

- **SQLite only**.
- Two separate database files:
  - `data/mycelium.db` — application data (currently only the minimal core `people` table)
  - `data/checkpoints.sqlite` — LangGraph checkpointer (AsyncSqliteSaver + aiosqlite for langgraph dev / Studio ASGI compatibility; sync callers go through run_query bridge)
- The shared storage layer must remain **dead simple**.
- Direct storage access by the supervisor is a **Phase 1 concession**, not the long-term target architecture.

See `src/storage/core.py` for the current minimal implementation.

---

## Public query flow (current)

Core storage holds only `id`, `name`, and `employer`. Callers send a query-only **`PersonQuery`** (`person_key`, optional `requested_attributes`). The graph state always includes `MyceliumGraphState.query`; LangSmith trace input therefore always shows a `query` section even for internal-only operations.

### Flow summary

| Intent | What the caller sends | Graph path (current / target) | What comes back |
|--------|----------------------|-------------------------------|-----------------|
| **Lookup (found)** | `person_key` (+ optional non-core attrs) | `supervisor` → `core_data_agent` → `CoreIdentity.find_by_key` | `results`: one or more core dicts (multiple when a name is ambiguous); plural `message` when N>1 |
| **Lookup (miss)** | `person_key`, no match | Same | `results`: `[]`; plain not-found `message` (no public ingest guidance) |
| **Non-core attrs** | `person_key` + e.g. `age`, `x_handle` | Same lookup; narrative only | `results`: core dict if person exists; `message` notes ongoing research |

### Response fields (query outcomes)

All external responses use the minimalist **`PersonResponse`** (`results`, `message`, `debug`, `trace_id`, `thread_id`):

- **`results`** — Factual core data only. Populated when a record exists; empty when lookup misses.
- **`message`** — Primary channel for humans and agents: found / not-found / non-core research narrative.
- **`debug`** — Internal context (original `person_key`, `requested_attributes`, outcome tags). Callers should not depend on it.
- **`trace_id`** — LangSmith trace identifier for this graph invocation when `LANGCHAIN_TRACING_V2` is enabled; otherwise `null`. Lets operators and developers jump from a JSON response to the matching trace in LangSmith for debugging. When creating your LangSmith API key, select **Personal Access Token (PAT)** (prefix `lsv2_pt_`). `LANGCHAIN_PROJECT` (default "mycelium") names the tracing project in the LangSmith UI — it will be created automatically on first use; no manual pre-creation required. See README.md for full setup steps.
- **`thread_id`** — Conversation/session identifier for this request. CLI and MCP callers may pass a stable `thread_id` to tie follow-up queries to the same LangGraph checkpoint thread; when omitted, the runtime generates one per invocation.

These correlation fields support **observability** (trace ↔ response) and **external agent sessions** (same `thread_id` across related MCP or CLI calls). They are set in `run_query` (`src/graphs/core.py`) after the graph finishes, not by individual response builders in the supervisor.

There is no separate `DataRequest` model or `status` enum — outcome is conveyed through `results` plus natural-language `message`.

### Future work: re-adding core data addition

Public ingest (CLI `ingest`, MCP `submit_person_data`, `PersonQuery.provided_data`, enrich/validator loop) was removed June 2026. Planned return:

- Internal coordination via specialist agents (including `core_data_agent` persist paths).
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

The goal for this phase is to build a working, minimal system that demonstrates:

- A supervisor that routes queries to core and specialist agents (core via `core_data_agent`)
- A very clean, minimal core people dataset
- An MCP interface that external agents use to **query** person data (addition returns via internal agents later)
- Clear separation of concerns that supports future growth into fully agent-owned data

See `TODO.md` for the current prioritized list of work.

---

**Last major update:** June 2026 (query-only migration 1000–1110 + niggle cleanup 1120)
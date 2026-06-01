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
  - `data/checkpoints.sqlite` — LangGraph checkpointer
- The shared storage layer must remain **dead simple**.
- Direct storage access by the supervisor is a **Phase 1 concession**, not the long-term target architecture.

See `src/storage/core.py` for the current minimal implementation.

---

## Core Ingestion Handshake (Phase 1)

Core storage holds only `id`, `name`, and `employer`. Lookups and ingests share the same **`PersonQuery`** shape; ingestion is triggered by including **`provided_data`** (MCP `submit_person_data` or CLI `ingest`). The flow is single-step: callers supply `name` and `employer` upfront (`id` optional — assigned after validation if empty).

### Flow summary

| Intent | What the caller sends | Graph path | What comes back |
|--------|----------------------|------------|-----------------|
| **Lookup** | `person_key` only | Supervisor reads storage | `results`: one core dict if found; neutral `message` |
| **Not found** | `person_key` only, no match | Supervisor only | `results`: `[]`; `message` states the miss and briefly notes how to ingest if desired |
| **Ingest** | `person_key` + `provided_data` | Supervisor → enrich (prepare) → validator → supervisor (persist) | `results`: core dict on success; `[]` on validation failure |

Enrich **prepares** the record (including id assignment). The supervisor **writes to SQLite only after** validation succeeds.

### Response fields (ingestion outcomes)

All external responses use the minimalist **`PersonResponse`** (`results`, `message`, `debug`):

- **`results`** — Factual core data only. Populated when a record exists or was just added; empty when lookup misses or ingest fails.
- **`message`** — Primary channel for humans and agents: found/not-found narrative, ingest guidance, success ("Added core record for …"), or failure ("Could not add core record: …").
- **`debug`** — Internal context (original `person_key`, `requested_attributes`, outcome tags). Callers should not depend on it.

There is no separate `DataRequest` model or `status` enum — outcome is conveyed through `results` plus natural-language `message`.

---

## Technical Foundation

- **Primary Framework**: LangGraph (Python) with explicit stateful graphs
- **Checkpointer**: SQLite (`langgraph-checkpoint-sqlite`)
- **Integration**: MCP server for external AI agents (JSON-only)
- **Language & Standards**: Python 3.12+, strict typing with Pydantic, high code quality
- **Observability**: LangSmith tracing from day one

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

- A supervisor that can route requests between core identity and specialist agents (initially stubbed)
- A very clean, minimal core people dataset
- An MCP interface that external agents can use to query and contribute person data
- Clear separation of concerns that supports future growth into fully agent-owned data

See `TODO.md` for the current prioritized list of work.

---

**Last major update:** June 2026 (following model alignment and workflow hardening work)
# Mycelium — Phase 1 MVP Direction

**Status:** Current working guidance (late May 2026)  
**Audience:** Cursor + implementation work  
**Related documents:**
- `docs/vision.md` (high-level project vision)
- `prompts/system/CORE_PROMPT.md` (core rules and philosophy)

---

## 1. Collaboration Model

- **Cursor** is the primary environment for writing, editing, and implementing code.
- **Grok Build** is used as a parallel partner for planning, architecture discussion, review, and exploration.
- The preferred flow is: Cursor does the majority of implementation work. Grok is consulted for plans, architectural decisions, reviews, and when stuck on direction.

## 2. Core Architectural Philosophy for Phase 1

This is the most important refinement from recent work:

**Everything is ultimately owned by specialist agents — including the "core" dataset.**

Key implications:

- The **supervisor** is a **coordinator and router**, not a direct data accessor or owner of data.
- Specialist agents own both the *responsibility* for a domain of data **and** the storage strategy for that data.
- Even basic **identity resolution** (finding a person by email, X handle, name, phone, or any non-stable identifier) may require querying one or more specialist agents rather than performing a direct database lookup.
- The supervisor detects what type of data is being requested, determines the appropriate specialist agent, and hands off the work (creating the agent if necessary).
- There are no "god agents." The supervisor must remain narrow and explicit in its responsibilities.

This represents a significant shift from earlier thinking that treated the core CRM table as a privileged, directly-queryable store.

## 3. Core Person Model (Strictly Minimal)

The core `Person` record is deliberately tiny:

```python
class Person(BaseModel):
    id: str
    name: str
    employer: str | None = None
```

**Rules for the core:**
- `CORE_PERSON_FIELDS = {"id", "name", "employer"}`
- `MINIMUM_VIABLE_FIELDS = ["name", "employer"]`
- `email`, `phone`, `title`, demographics, social handles, and all other attributes are **not** part of the core model.
- There is **no `extra` field** on `Person`. Anything that doesn't belong in the absolute minimum core belongs to a specialist agent.

The `Person` model should only represent records that live in the primary core `people` table.

## 4. Derivative Data and Specialist Agents

- We **explicitly do not pre-define** derivative attributes, dataset types, or storage structures.
- The supervisor is responsible for classifying requested data and routing it to the correct specialist agent.
- If no suitable agent exists for a data type (e.g., "demographics"), the system should eventually support creating one.
- How a specialist agent stores and manages its data is **not** defined centrally. Each agent can choose its own approach.

**Current practical rule for Phase 1:**
- Do not create shared tables or infrastructure for "derivative datasets" in the core storage layer.
- When the supervisor encounters non-core attributes, it should note this in the audit log and response rather than trying to create formal derivative dataset records.

## 5. Storage Constraints (Phase 1)

- **SQLite only**.
- Two separate database files:
  - `data/mycelium.db` — application data (currently only the minimal core `people` table)
  - `data/checkpoints.sqlite` — LangGraph checkpointer (via `langgraph-checkpoint-sqlite`)
- The shared storage layer (`CoreStorage`) must remain **dead simple**. It should only manage the core `people` table with columns for `id`, `name`, and `employer`.
- Direct storage access is a **Phase 1 concession**, not the target long-term architecture.

See the current implementation in `src/storage/core.py` for the expected level of minimalism.

## 6. Known Inconsistencies and Cleanup Items

The following areas are currently out of alignment with the direction above and need to be addressed:

- `DerivativeDatasetRef` model in `src/models/state.py`
- `PersonResponse` statuses such as `derivative_pending`
- Any supervisor logic that creates or manages "derivative datasets"
- Old references to pre-defined derivative attributes (e.g., any remaining `DERIVATIVE_ONLY_ATTRIBUTES` style constants or logic)
- `Person` model and storage schema still containing fields that should no longer be in core

These should be simplified as implementation proceeds.

## 7. Other Phase 1 Technical Constraints

- Use SQLite checkpointer (`langgraph-checkpoint-sqlite`)
- MCP server (using FastMCP) is the primary interface for external AI agents
- All I/O with external agents is JSON
- Strict typing with Pydantic + mypy must pass cleanly
- Maintain the supervisor + specialist agent pattern (no god agents)
- Include basic LangSmith tracing hooks where practical

## 8. Implementation Guidance

When writing or reviewing code, ask these questions:

- Does this code assume the supervisor (or a shared storage layer) owns or structures derivative data? If yes, reconsider.
- Are we pre-defining how a particular type of data will be stored or organized? If yes, push the decision to the relevant specialist agent.
- Is the `Person` model or the core `people` table staying strictly minimal?
- Is the supervisor doing coordination/routing, or is it taking on data ownership responsibilities?

When in doubt about modeling, default to deferring to future specialist agents rather than building centralized structures.

## 9. Current Phase 1 Focus

The goal for this phase is to build a working, minimal system that demonstrates:

- A supervisor that can route requests between core identity and specialist agents (initially stubbed)
- A very clean, minimal core people dataset
- An MCP interface that external agents can use to query and contribute person data
- Clear separation of concerns that supports future growth into fully agent-owned data

This document should be treated as the active implementation guide for Phase 1 work.

---

**Last major update:** Late May 2026
```

---

Now I'll update `vision.md` to reference this new document and align the high-level view.
# Mycelium — Project Brief (original vision)

> **For agents:** Prefer **[CORE_PROMPT.md](CORE_PROMPT.md)** for rules and philosophy, and **[docs/architecture.md](../../docs/architecture.md)** for current design, flows, and storage. This file preserves the original vision; the bootstrap section below is **historical** (completed).

You are helping me build Mycelium — a maintainable LangGraph-based prototype for AI-managed data sources.

## Project vision

Mycelium is a system where AI agents autonomously handle data ingestion, schema evolution, validation, indexing, and continuous self-improvement. Data sources will be 100% managed by AI instead of humans.

## Core requirements (still valid)

- LangGraph (Python) with explicit graphs, nodes, edges, and persistent state.
- Strong emphasis on maintainability, type safety, observability, and avoiding agent drift.
- Python 3.12+, Pydantic, strict typing.
- No god-agents or free-form PM agents.
- LangSmith for tracing from day one.
- Small, reviewable changes only; clean architecture over rapid hacking.

## Current implementation (June 2026)

- **Public interface:** Query-only CLI and MCP (`PersonQuery`: `person_key`, optional `requested_attributes`). Data addition returns via internal agent coordination, not caller-supplied payloads.
- **Graph:** `supervisor` → `build_context` → `invoke_specialists` → `assemble_response` (see `src/graphs/core.py`).
- **Specialists:** Generated per attribute domain (Agent Factory); not the original Ingest/Validator bootstrap agents.
- **Checkpointer:** SQLite (`data/checkpoints.sqlite`), not Postgres.
- **Data:** JSON flat files for seed, classification, registry, and specialist storage; SQLite is for checkpoints (and legacy DB compatibility only). See `docs/architecture.md`.

## Project rules (enforce strictly)

- Modular folder structure: `src/agents/`, `src/graphs/`, `src/tools/`, `src/models/`, `src/storage/`, `tests/`, `prompts/`, `docs/`
- All code must be type-hinted, well-documented, with pytest where appropriate.

## Historical — bootstrap tasks (done)

These were the first milestones; the repo has moved past them:

1. Initialize Python project (`pyproject.toml`, uv, `.gitignore`, README).
2. Cursor rules under `.cursor/rules/`.
3. Core dependencies: langgraph, langchain, langsmith, pydantic, etc. (not psycopg for app data).
4. Minimal LangGraph with supervisor + specialists (evolved beyond Ingest/Validator).
5. README with architecture diagram and run instructions.

Work step-by-step. Show a plan first for non-trivial work, then implement incrementally. Prioritize long-term maintainability.
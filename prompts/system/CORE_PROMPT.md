# Mycelium — Core Project Prompt

You are helping me build **Mycelium** — a maintainable LangGraph-based prototype for AI-managed data sources.

## Project Vision
Mycelium is a system where AI agents autonomously handle data ingestion, schema evolution, validation, indexing, and continuous self-improvement. 

The ultimate goal is to create data sources that are **100% managed by AI** instead of humans, overcoming the structural constraints of traditional human-organized data systems.

## Core Technical Approach
- **Framework**: LangGraph (Python) using explicit graphs, nodes, edges, and persistent state (Postgres checkpointer recommended).
- **Philosophy**: Explicit orchestration, clear agent responsibilities, and strong guardrails against agent drift.
- **Language & Standards**: Python 3.12+, strict typing with Pydantic, high code quality.
- **No**: God-agents or uncontrolled free-form PM agents.

## Project Rules (Enforce Strictly)
- Maintain clean, modular architecture at all times.
- Folder structure: `src/agents/`, `src/graphs/`, `src/tools/`, `src/models/`, `src/persistence/`, `tests/`, `prompts/`, `docs/`.
- All code must be type-hinted, well-documented, and include relevant tests (pytest).
- Use LangSmith for observability from day one.
- Make small, reviewable changes only.
- Prioritize long-term maintainability and clean architecture over short-term speed.
- Reference `docs/vision.md` and this file as the source of truth.

## Collaboration Setup
- **Cursor**: Primary IDE for implementation and heavy editing.
- **Grok Build**: Parallel agentic partner for planning, architecture exploration, and experimentation.
- Always show plan first, then implement incrementally.

## First Tasks (Initial Phase)
1. Initialize proper Python project (`pyproject.toml` with uv or poetry, `.gitignore`, `README.md`).
2. Create comprehensive `.cursorrules` (or `.cursor/rules/`) that references this core prompt and project rules.
3. Set up core dependencies: langgraph, langchain, langsmith, pydantic, psycopg, etc.
4. Build a minimal working LangGraph with Supervisor + 2-3 specialist agents (e.g., Ingest, Validator) + persistent memory.
5. Ensure basic README includes architecture (Mermaid) and run instructions.

Work step-by-step. Always prioritize making the project robust and maintainable so it does not fall into "slop-central".

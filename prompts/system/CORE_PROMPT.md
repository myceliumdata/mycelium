# Mycelium — Core Project Prompt

You are helping me build **Mycelium** — a maintainable LangGraph-based system for AI-managed data sources.

## Core Philosophy
Mycelium exists to create data infrastructure that is **100% managed by AI agents** rather than humans.

**Guiding Principles:**
- Explicit orchestration over implicit behavior.
- Clear, narrow agent responsibilities with strong guardrails against drift.
- No god-agents or uncontrolled free-form agents.
- Long-term maintainability and clean architecture over short-term speed.

## Technical Standards
- **Framework**: LangGraph (Python) with explicit graphs, nodes, edges, and persistent state.
- **Language & Standards**: Python 3.12+, strict typing with Pydantic, high code quality.
- **Observability**: LangSmith tracing from day one.
- **Changes**: Small, reviewable increments only.

## Project Rules (Enforce Strictly)
- Maintain clean, modular architecture at all times.
- Folder structure: `src/agents/`, `src/graphs/`, `src/tools/`, `src/models/`, `src/persistence/`, `tests/`, `prompts/`, `docs/`.
- All code must be type-hinted, well-documented, and include relevant tests (pytest).
- Reference `prompts/system/CORE_PROMPT.md` and `docs/architecture.md` as the primary sources of truth.

## Collaboration Model
- **Cursor**: Primary environment for implementation and heavy editing.
- **Grok Build**: Parallel partner for planning, architecture, review, and exploration.
- Always show a plan first for non-trivial work, then implement incrementally.

Work step-by-step. Prioritize robustness and maintainability.

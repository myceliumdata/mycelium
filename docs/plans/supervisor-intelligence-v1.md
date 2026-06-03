# Plan: Add Intelligence to the Supervisor (Dynamic LLM Classification + Agent Creation)

## Context & Vision Alignment
The Mycelium project aims to build data sources that are 100% managed and organized by AI systems rather than humans. The Supervisor is the central orchestrator. We are now evolving it into a truly intelligent router and dynamic system builder.

**Core Requirements:**
1. **Intelligent Classification**: Use an LLM to analyze incoming data/requests and determine the correct category/domain.
2. **Dynamic Agent Creation**: When a category does not have a dedicated specialist agent yet, the Supervisor should create one on the fly (code generation + registration).

## Goals
- Accurate, explainable routing.
- Graceful handling of novel data types with zero manual intervention.
- Modular, observable, and safe architecture.
- Primary language: Python.

## High-Level Architecture

**New/Enhanced Components:**
1. **Classification Engine**
   - LLM call with structured output (category, confidence, reasoning).
   - Evolving category taxonomy (vector DB or graph).

2. **Agent Factory**
   - LLM-assisted + template-based code generation.
   - Automatic registration and initialization.
   - Strong safety/sandboxing layer.

3. **Enhanced Supervisor**
   - Intelligent routing logic with confidence thresholds.
   - Fallback + creation triggers.

4. **Category Knowledge Base**
   - Persistent store of known categories + examples.

## Alternatives Considered
- Pure static/manual: Too limiting for the vision.
- Embedding-only similarity: Fast but weak on novel categories.
- Heavy frameworks (LangGraph/CrewAI): Powerful but adds complexity.
- **Recommended**: Hybrid LLM classification + templated generation.

**Stack**: Python 3.11+, LiteLLM (for model flexibility), Pydantic, Jinja2 templates.

## Short Summary of High-Level Steps
1. Design category taxonomy + classification prompts.
2. Implement Classification Engine.
3. Build Category Knowledge Base.
4. Create Agent Factory with safe code gen.
5. Upgrade Supervisor routing + creation logic.
6. Add observability, safety guardrails, and testing.

## Risks & Mitigations
- Hallucinated categories → Confidence thresholds + human fallback option.
- Unsafe generated code → Sandboxing (restricted exec, subprocess, or Docker).
- Agent proliferation → Uniqueness checks and rate limits.
- Cost/latency → Caching + tiered models.

## Success Criteria
- Correct classification of both known and novel data.
- Automatic creation of functional specialist agents.
- System remains stable and debuggable.

## Next Steps After Approval
- Break this into detailed implementation tasks.
- Start with Phase 1 (Classification).

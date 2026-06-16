# Mycelium Prototype - Second Example with Lahman Baseball Database

> **Ur artifact** (June 2026) — preserved original Grok design brief. **Source of truth:** [`baseball-example-program.md`](baseball-example-program.md).

**Goal**: Build an AI-managed autonomous data infrastructure example using the Lahman Baseball Database. Demonstrate shifting from human-organized static data to fully agent-managed sources with discovery, ingestion, derivation, and provenance.

## Background
- **Dataset**: Lahman Baseball Database (CSVs from https://sabr.org/lahman-database/, stats 1871–2025). Small (~10-20 MB uncompressed), clean, tabular—ideal for prototyping.
- **New Concepts**:
  1. **Background data via URLs**: Agents handle source URLs (download, docs, glossaries). Use taxonomy tags to route to specialist agents.
  2. **Derivative/Derived Data**: Aggregations, computations, enrichments (e.g., career totals, batting averages, trends).
  3. **Provenance/Lineage**: Every derived item links to original base data + computation reference (code/function/commit) + metadata (time, agent, params).

## Architecture Preferences
- Python-first.
- Lightweight local storage: SQLite or DuckDB for base tables + derived tables + provenance metadata.
- Agent orchestration: LangGraph (or equivalent) with specialist agents (Ingestion, Taxonomy Router, Derivation, Query/Reasoning).
- Modular, observable, reproducible, auditable.
- Design-first: Schemas, workflows, skeletons. Avoid full app; produce iterative starter.

## Deliverables
1. Overall system design (text/Mermaid diagram).
2. Database schema (base, derived, provenance).
3. Agent roles and workflows.
4. Python code skeletons (ingestion, derivation with provenance, query).
5. 3–5 concrete baseball-derived query examples.
6. Recommended next iteration steps.

Focus on clarity, modularity, and quick executability with Lahman. Support natural questions with full traceability.

**User Context**: Experienced engineer (C, Obj-C, Eiffel, Python). Will refine iteratively.
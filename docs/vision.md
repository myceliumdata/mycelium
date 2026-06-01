# Mycelium — Project Vision

## Overview
Mycelium is an AI-native data management system in which intelligent agents autonomously organize, evolve, and maintain data sources.

The system uses a network of LangGraph agents that handle ingestion, schema evolution, validation, indexing, and continuous self-improvement — creating living, self-organizing information ecosystems.

## Core Motivation
Current data sources are organized by humans for humans, imposing significant structural and scalability constraints. Mycelium aims to build data infrastructure that is **100% managed by AI**, removing those legacy limitations.

## Target Capabilities
- Autonomous schema inference and evolution
- Intelligent multi-source ingestion
- Continuous data validation and quality control
- Self-optimizing indexing and retrieval patterns
- Emergent discovery of connections across datasets
- Human-in-the-loop only for high-level guidance

## Technical Foundation
- **Primary Framework**: LangGraph (Python) with explicit stateful graphs and SQLite checkpointers
- **Storage**: SQLite only. Two databases — one minimal core `people` table (`mycelium.db`) and one for LangGraph checkpoints (`checkpoints.sqlite`)
- **Integration**: MCP server for external AI agents; JSON-only I/O
- Strong emphasis on modularity, type safety (Pydantic), and observability (LangSmith)
- Designed for maintainability and controlled experimentation

> **Important**: See [docs/phase-1-direction.md](phase-1-direction.md) for the current detailed implementation guidance, especially the refined model that all data (including core) is ultimately owned by specialist agents.

## Success Definition
Mycelium will be successful when it can accept raw or semi-structured data and, with minimal ongoing human input, produce clean, queryable, and continuously improving knowledge bases.

## Current Status
**Date**: May 31, 2026  
**Phase**: Phase 1 MVP — Minimal supervisor + specialist agent graph with an extremely narrow core `people` dataset (id + name + employer only). SQLite persistence, MCP server for external agents, and CLI.

See [docs/phase-1-direction.md](phase-1-direction.md) for detailed current implementation guidance.

This vision will be refined iteratively as the prototype evolves.

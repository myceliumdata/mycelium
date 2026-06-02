# Mycelium — TODO

This file tracks open tasks, decisions, and technical debt.

**Note for Paul:**  
`docs/architecture.md` is the current source of truth for Phase 1 direction.  
We now direct Cursor (as a senior developer) using structured prompts located in `prompts/cursor/next/`. See `prompts/WORKFLOW.md` for the full protocol.

The tasks in this document represent the long-term shared TODO between Grok and Paul. When we agree on work, we create a prompt in `prompts/cursor/next/` for Cursor to execute.

## High Priority / Near Term

### Codebase Catch-up to Current Direction

The code was written before several key decisions were finalized. The following work is needed to bring the implementation in line with `docs/architecture.md`.

- [x] **Review and simplify `DerivativeDatasetRef`** in `src/models/state.py` — removed; use `deferred_attributes` + `specialist_required` (prompt `2025-06-01-1700-clean-derivative-references`).
- [x] Remove derivative dataset tables/methods from `src/storage/core.py` — core `people` table is id/name/employer only (same prompt).
- [x] Update `PersonResponse` statuses — `derivative_pending` replaced with `specialist_required`.
- [x] Refactor the supervisor to act as coordinator/router with delegated identity access (`2026-06-02-1100-supervisor-as-coordinator-router`).
- [x] Rename `orchestrator_agent` / related files to `supervisor` for consistency with the direction document (`2025-06-01-1730-rename-orchestrator-to-supervisor`).
- [x] Audit `src/models/state.py` — removed `DERIVATIVE_ONLY_ATTRIBUTES`; added `non_core_attributes()`.
- [x] Ensure the `Person` model and all code that constructs it only ever uses `id`, `name`, and `employer`.
- [x] Update tests and CLI/MCP response handling for `specialist_required` (same prompt).
- [x] **Minimal `PersonResponse`** — `results`, `message`, `debug` only (`2026-06-01-1912-redesign-response-model-light-minimalist`).
- [x] **Ingestion handshake** — single-step `provided_data` flow via enrich/validator (`2026-06-02-1000-redesign-ingestion-handshake`) — **removed from public API** June 2026 (`2026-06-05-1000`–`1050`).

**Goal:** The codebase reflects query-only public interfaces; the supervisor coordinates specialists; shared storage owns only the tiny core `people` table.

### Supervisor / specialist follow-ups

- [x] Query-only public surface (`PersonQuery`, CLI, MCP) — tasks `2026-06-05-1000`–`1050`.
- [x] `core_data_agent` specialist module (`2026-06-05-1060`).
- [x] Wire `core_data_agent` into graph; supervisor routes to it (`1070`, `1100`).
- [ ] Continue reducing inline routing lookups in `routing.py` now that core data node owns lookups.
- [ ] Further narrow response construction or move it behind specialist-specific builders.

### Re-adding data addition (internal / future — not public yet)

- [ ] Design internal coordination for adding core records (no `provided_data` on public `PersonQuery`).
- [ ] Persist path on `core_data_agent` (post-validation, specialist-owned).
- [ ] Stronger validation for new records (beyond former minimum-viable checks).
- [ ] Consider whether addition should trigger enrichment or specialist work.
- [ ] Re-evaluate machine-readable `status` or error categories for addition failures.
- [x] Clean up dead code from pre-1912 response model (`2026-06-02-1010-cleanup-dead-code-post-response-redesign`).

## Data

- [x] **Initial real seed** — `data/seed_crm.json` built from `data/raw_data.json` (457 people after dedup rules; backup at `data/seed_crm.json.bak`). Task: `2026-06-01-1730-process-raw-data-to-seed-crm`. To load the new seed locally, delete `data/mycelium.db` and restart.

## Observability (LangSmith / tracing)

- [x] `trace_id` + `thread_id` on `PersonResponse` (09xx series).
- [x] `get_langsmith_trace_url` helper (0980); README/architecture tracing notes.
- [ ] End-to-end LangSmith verification in Paul's environment (`.env`, CLI/MCP smoke with tracing on). Note: CLI now exits promptly (defensive cleanup + atexit).


## Other Near-Term Items

- [ ] Add a proper LICENSE file (currently deferred — see note below)

## Licensing

**Status:** Deferred

We intentionally skipped adding a LICENSE during the initial GitHub push (May 2026). This needs to be addressed before any public release or significant external usage.

Options to consider later:
- MIT (most permissive, common default)
- Apache 2.0
- Other

Decision owner: Paul

## Architecture & Design

- [ ] Decide on long-term strategy for the MCP server (keep in-repo vs extract later)
- [ ] Define clear boundaries between core agent logic and interface layers (MCP, CLI, etc.)
- [ ] Evaluate whether the current `CoreStorage` singleton pattern should be replaced with dependency injection once we have multiple agents accessing storage

## Infrastructure

- [ ] Set up GitHub Actions for linting (ruff), type checking (mypy), and tests  
  **Note (Paul, May 2026):** For now, run everything locally. Do not make CI required or blocking. Add the workflows as a foundation, but keep them optional/manual until the core logic has stabilized.
- [ ] Decide on release / versioning strategy

## Testing

- [x] Split tests into fast smoke (run frequently with `pytest -m smoke`) and full integration (run infrequently with plain `pytest` at end of major changes). See test files for `@pytest.mark.smoke` / `@pytest.mark.full`, README, and "Test Execution Policy" section in `prompts/cursor/WORKFLOW.md`. Cursor must default to smoke tests only, unless adding a full-suite test (in which case run it immediately). Grok determines the category for any new test. (addressed 2026-06)

## Documentation

- [ ] Keep `docs/architecture.md` up to date as the active implementation guide
- [x] Remove outdated derivative-dataset language from README, docs, and user-facing comments (`2025-06-01-1735-documentation-cleanup-old-derivative-language`).
- [x] Document legacy `data/mycelium.db` options for users upgrading from the old schema (`2025-06-01-1740-local-database-legacy-schema-note`).
- [ ] Expand README with clearer run instructions and architecture overview (partially addressed by 1735/1740)

## Process & Tooling (Grok + Paul)

- [ ] Refine the Cursor prompting workflow in `prompts/WORKFLOW.md` as we gain experience
- [ ] Decide on long-term location and retention policy for `prompts/cursor/done/` artifacts
- [ ] Consider adding lightweight tooling later (e.g. a script to list open prompts, generate status, etc.)

---

Last updated: 2026-06-05 (docs/reset niggle cleanup; task 1120)
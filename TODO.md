# Mycelium — TODO

This file tracks open tasks, decisions, and technical debt.

**Note for Paul:**  
`docs/phase-1-direction.md` is the current source of truth for Phase 1 direction.  
We now direct Cursor (as a senior developer) using structured prompts located in `prompts/next/`. See `prompts/WORKFLOW.md` for the full protocol.

The tasks in this document represent the long-term shared TODO between Grok and Paul. When we agree on work, we create a prompt in `prompts/next/` for Cursor to execute.

## High Priority / Near Term

### Codebase Catch-up to Current Direction

The code was written before several key decisions were finalized. The following work is needed to bring the implementation in line with `docs/phase-1-direction.md`.

- [x] **Review and simplify `DerivativeDatasetRef`** in `src/models/state.py` — removed; use `deferred_attributes` + `specialist_required` (prompt `2025-06-01-1700-clean-derivative-references`).
- [x] Remove derivative dataset tables/methods from `src/storage/core.py` — core `people` table is id/name/employer only (same prompt).
- [x] Update `PersonResponse` statuses — `derivative_pending` replaced with `specialist_required`.
- [ ] Refactor the supervisor (currently in `src/agents/orchestrator.py`) so it acts strictly as a coordinator/router rather than owning data decisions or creating derivative records.
- [ ] Rename `orchestrator_agent` / related files to `supervisor` for consistency with the direction document.
- [x] Audit `src/models/state.py` — removed `DERIVATIVE_ONLY_ATTRIBUTES`; added `non_core_attributes()`.
- [x] Ensure the `Person` model and all code that constructs it only ever uses `id`, `name`, and `employer`.
- [x] Update tests and CLI/MCP response handling for `specialist_required` (same prompt).

**Goal:** After this work, the codebase should clearly reflect that the supervisor coordinates specialist agents, and the only thing the shared storage layer owns is the tiny core `people` table.

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

## Documentation

- [ ] Keep `docs/phase-1-direction.md` up to date as the active implementation guide
- [ ] Expand README with clearer run instructions and architecture overview

## Process & Tooling (Grok + Paul)

- [ ] Refine the Cursor prompting workflow in `prompts/WORKFLOW.md` as we gain experience
- [ ] Decide on long-term location and retention policy for `prompts/done/` artifacts
- [ ] Consider adding lightweight tooling later (e.g. a script to list open prompts, generate status, etc.)

---

Last updated: May 31, 2026 (instructions prepared for Cursor / Paul)
```

Now I need to create the GitHub repository using the tool.
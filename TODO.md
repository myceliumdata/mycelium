# Mycelium — TODO

This file tracks open tasks, decisions, and technical debt.

## High Priority / Near Term

- [ ] Add a proper LICENSE file (currently deferred — see note below)
- [ ] Review and clean up `DerivativeDatasetRef` usage and related response statuses in `src/models/state.py`
- [ ] Align supervisor logic with the "agents own their data" model (no pre-creation of derivative datasets in shared storage)
- [ ] Update `PersonResponse` statuses and `orchestrator` / supervisor behavior to match current Phase 1 direction
- [ ] Improve identity resolution strategy (how the supervisor handles lookups by email, name, etc. when core only stores id + name + employer)

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
- [ ] Consider adding a basic CI workflow that runs on push/PR
- [ ] Decide on release / versioning strategy

## Documentation

- [ ] Keep `docs/phase-1-direction.md` up to date as the active implementation guide
- [ ] Expand README with clearer run instructions and architecture overview

---

Last updated: May 31, 2026
```

Now I need to create the GitHub repository using the tool.
# Mycelium — Context Reset (current MVP, June 2026)

**Date:** 2026-06-05  
**Last Updated:** 2026-06-05 (post 1120 niggle cleanup)  
**Purpose:** Canonical fast context load for fresh sessions (`cat` this file at session start)

---

## Vision & Core Philosophy

Mycelium creates **AI-native, self-managing data sources** where **100% of the infrastructure is managed by AI agents** (not humans). External agents use the MCP server (JSON).

**All data is agent-owned** (including the "core"):
- The **Supervisor** is a pure **coordinator/router** — never a data owner or direct accessor.
- Specialist agents own both responsibility *and* their own storage strategy.
- No pre-defined derivatives or storage structures — they emerge from agents.
- No god-agents; supervisor stays narrow and explicit.

**Phase 1 rule:** Keep shared storage dead simple. See `docs/architecture.md`.

## Phase 1 MVP — Strictly Minimal Core

- `Person`: **only** `id`, `name`, `employer`
- `CORE_PERSON_FIELDS = {"id", "name", "employer"}`
- `MINIMUM_VIABLE_FIELDS = ["name", "employer"]`
- Everything else is non-core → specialists (future).

## Public interface (query-only, complete)

- **Graph:** `START → supervisor (route="core_data") → core_data_agent → END`
- **CLI:** `query`, `seed` only
- **MCP:** `query_person`, `list_specialist_routing`
- **PersonQuery:** `person_key`, `requested_attributes` — no `provided_data`
- Legacy **enrich/validator/person_prep** on disk, unwired, for future internal addition

Migration tasks **1000–1110** complete; doc/tmp/reset polish **1120** complete.

## Collaboration & Cursor Workflow

**Paul:** vision/priorities. **Grok:** planning, reviews, prompts. **Cursor:** senior developer via prompts.

See `prompts/cursor/WORKFLOW.md` and `.cursor/rules/04-cursor-workflow.mdc`:

- `next/` → claim to `in-progress/` → deliver to `done/<slug>/` → remove only your claim from `in-progress/`.

## Must-Read Files (every session start)

1. `docs/architecture.md` — primary source of truth
2. `prompts/cursor/WORKFLOW.md`
3. `TODO.md`
4. `prompts/system/CORE_PROMPT.md`
5. `.cursor/rules/` (esp. 04-cursor-workflow.mdc)

## Working Principles

- Scope discipline mandatory; small reviewable diffs
- Prefer simplification/deletion
- `docs/architecture.md` is active truth
- Treat Cursor as senior developer

---

## Current Task

**Next objective:** Supervisor/specialist follow-ups and observability from `TODO.md`:

- Reduce duplicated lookup logic in `routing.py` (now that `core_data_agent` owns the graph path)
- Narrow response construction / specialist-specific builders
- Design **internal** data addition (no public `provided_data`; see TODO "Re-adding data addition")
- LangSmith E2E in operator environment (`.env`, CLI/MCP with tracing on)
- License, optional CI, real non-core specialists

**Context:** Query-only public surface is stable. Checkpoint serde warnings addressed via `JsonPlusSerializer(allowed_msgpack_modules=...)` in `graphs/core.py`.

**References:** `docs/full-code-walkthrough.md`, `prompts/cursor/done/2026-06-05-1110-*/review.md`, task 1120 output.

**Suggested approach:** Add focused prompts under `prompts/cursor/next/` per TODO item; claim one at a time per WORKFLOW.md.

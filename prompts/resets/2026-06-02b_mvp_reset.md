# Mycelium — Context Reset Prompt (MVP Phase) [Compact]

**Date:** 2026-06-05  
**Last Updated:** 2026-06-05 (1120)  
**Purpose:** Fast context load for fresh sessions

---

## Vision & Core Philosophy

Mycelium creates **AI-native, self-managing data sources** where **100% of the infrastructure is managed by AI agents** (not humans). External agents use the MCP server (JSON).

**All data is agent-owned** (including the "core"):
- The **Supervisor** is a pure **coordinator/router** — never a data owner or direct accessor.
- Specialist agents own both responsibility *and* their own storage strategy.
- Even identity resolution may route through specialists.
- No pre-defined derivatives or storage structures — they emerge from agents.
- No god-agents; supervisor stays narrow and explicit.

**Phase 1 Rule:** Keep shared storage dead simple. Supervisor direct access is a temporary concession only.

See `docs/architecture.md`.

## Phase 1 MVP — Strictly Minimal Core

**Core Data Model:**
- `Person`: **only** `id`, `name`, `employer`
- `CORE_PERSON_FIELDS = {"id", "name", "employer"}`
- `MINIMUM_VIABLE_FIELDS = ["name", "employer"]`
- Everything else is non-core and routed to specialists.

**Key Architecture:** See `docs/architecture.md`.

## Collaboration & Cursor Workflow

**Paul**: Vision/priorities. **Grok**: Planning, reviews, prompts. **Cursor**: Senior developer via prompts.

**Cursor Handoff** (see `prompts/cursor/WORKFLOW.md` + `.cursor/rules/04-cursor-workflow.mdc`):

- `next/`: Ready tasks.
- `in-progress/`: Claimed (the lock).
- `done/`: Artifacts (`prompt.md`, `output.md`, `review.md`).

**When told "Work on the next task":**
1. Scan `prompts/cursor/next/`, sort alphabetically (oldest first).
2. **Immediately move** first item to `in-progress/` (claim).
3. Execute per prompt (strict scope).
4. Deliver to `done/<name>/`.
5. **Remove only your claimed item** from `in-progress/`. Never touch others (parallel safety).

**Scope Discipline:** Out-of-scope? Stop, document, create follow-up prompt. **Cursor Config:** `.cursor/rules/` (langgraph, python, workflow).

## Must-Read Files (Every Session Start)

1. `docs/architecture.md` — **Primary source of truth**.
2. `prompts/cursor/WORKFLOW.md` — Full protocol + safety.
3. `TODO.md` — Priorities.
4. `prompts/system/CORE_PROMPT.md` — Principles.
5. `.cursor/rules/` (esp. 04-cursor-workflow.mdc) — Embedded instructions.

## Working Principles

- Scope discipline mandatory.
- Prefer simplification/deletion.
- Small, reviewable changes.
- `docs/architecture.md` is active truth.
- Treat Cursor as senior developer.

---

## Current Task

**Next Objective:** Supervisor/specialist follow-ups from `TODO.md` (routing reduction in `routing.py`, response-builder narrowing, internal data-addition design, LangSmith E2E). See also `prompts/resets/2026-06-05_mvp_current.md` for the canonical reset.

**Context / Constraints:** Query-only migration (`1000`–`1110`) and niggle cleanup (`1120`) are complete. Graph: supervisor → `core_data_agent`. Legacy enrich/validator/person_prep unwired.

**Success Criteria (1120):**  
- [x] `docs/architecture.md` and `docs/full-code-walkthrough.md` — no "pending 1070/1100" or transitional graph language.
- [x] `tmp/restart-server-for-schema.md` query-only; ingest teaching files removed (1110).
- [x] Resets refreshed; `2026-06-05_mvp_current.md` added.
- [x] Checkpoint "Deserializing unregistered type" warnings addressed (`JsonPlusSerializer` allowlist in `graphs/core.py`).
- [x] Tests (smoke for frequent, full for end-of-changeset), linter, CLI/graph smokes pass. (See split in README, pyproject markers, and "Test Execution Policy" in WORKFLOW.md. Cursor: default to smoke; run full immediately for any new full test added. Grok determines the category for any new test. CLI now exits promptly thanks to defensive finally + atexit.)


**Relevant Files / References:** `prompts/cursor/done/2026-06-05-1110-*/review.md`, `1120` output, `docs/architecture.md`, `TODO.md`.

**Suggested Approach:** New prompts in `next/` per TODO; one task at a time per WORKFLOW.md.
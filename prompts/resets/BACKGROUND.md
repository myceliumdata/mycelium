# Mycelium — Background reading list (session restart)

**Purpose:** When Paul starts a **new Grok (or agent) session**, paste or point to this file first. Read everything in **Tier 1** before substantive work. Use Tier 2–3 as needed for the task at hand.

**Do not summarize away details** in these docs — they are the source of truth for architecture, workflow, and constraints.

---

## How to use this file

1. Read **Tier 1** in order (read-only tools: `read_file`, `list_dir`, `grep`; inspection shell only).
2. Read the **latest dated context prompt** in `prompts/resets/` matching the current thread (filename `YYYY-MM-DD_*.md`, newest relevant).
3. Confirm to Paul: which docs you read, and that you are ready — then wait for explicit instructions unless he asked for a specific action.

---

## Tier 1 — Always read (project onboarding)

| Document | Why |
|----------|-----|
| [PROJECT_BRIEF.md](../../PROJECT_BRIEF.md) | Entry pointer to canonical briefs |
| [prompts/system/CORE_PROMPT.md](../system/CORE_PROMPT.md) | Philosophy, rules, storage summary, collaboration |
| [prompts/system/PROJECT_BRIEF.md](../system/PROJECT_BRIEF.md) | Original vision + historical bootstrap notes |
| [README.md](../../README.md) | How to run CLI/MCP, tracing, Studio, response shape |
| [docs/architecture.md](../../docs/architecture.md) | **Living** architecture, graph flow, storage, query outcomes |
| [prompts/cursor/WORKFLOW.md](../cursor/WORKFLOW.md) | Cursor handoffs: `next/` → `in-progress/` → `done/` |
| [.cursor/rules/](../../.cursor/rules/) | Cursor automation (especially `04-cursor-workflow.mdc` if present) |

---

## Tier 2 — Read for implementation / review work

| Document | When |
|----------|------|
| [docs/full-code-walkthrough.md](../../docs/full-code-walkthrough.md) | Navigating the codebase end-to-end |
| [docs/database-notes.md](../../docs/database-notes.md) | SQLite / legacy DB / seed paths |
| [docs/plans/seed-data-context-architecture.md](../../docs/plans/seed-data-context-architecture.md) | Seed JSON, context union, graph nodes (redesign) |
| [docs/plans/classification-engine-phase1.md](../../docs/plans/classification-engine-phase1.md) | Category tree, supervisor classification |
| [docs/plans/agent-factory-phase2.md](../../docs/plans/agent-factory-phase2.md) | Dynamic specialists, registry, template |
| [docs/plans/supervisor-intelligence-v1.md](../../docs/plans/supervisor-intelligence-v1.md) | Phased intelligence roadmap |
| [TODO.md](../../TODO.md) | Tracked follow-ups |

---

## Tier 3 — Thread-specific resets (read when resuming that work)

| Document | Thread |
|----------|--------|
| [2026-06-07_redesign_reset.md](2026-06-07_redesign_reset.md) | Seed-data-context redesign slices 1500–1720 |
| [2026-06-09_full_context_reset.md](2026-06-09_full_context_reset.md) | Strict read-only restart after backout (historical) |
| [2026-06-04_specialist-research-planning.md](2026-06-04_specialist-research-planning.md) | **Current:** specialist LLM + Tavily research (Phase 1 plan) |

---

## Cursor queue (inspect, do not assume)

After reading tiers above:

- `list_dir` → `prompts/cursor/next/` (oldest filename = next task)
- `list_dir` → `prompts/cursor/in-progress/`
- Recent `prompts/cursor/done/<slice>/` for the area you are reviewing

---

## Collaboration rules (enforce every session)

- **Paul + Grok:** planning, architecture, design docs, review, Cursor prompt authoring.
- **Cursor:** implementation from prompts in `prompts/cursor/next/` (claim per WORKFLOW).
- **Grok must not write or edit source code** unless Paul explicitly authorizes implementation in that message.
- **Design before code:** agree plan in `docs/plans/` before Cursor slices or Grok patches.
- **Small, reviewable changes;** no god-agents; supervisor stays thin.
- **Tests:** smoke by default during dev; full suite for major changesets (see WORKFLOW + README).

---

## Quick structural map

```
data/seed.json, data/categories.json, data/agent_registry.json, data/agents/<cat>/
src/agents/   supervisor, classification/, factory/, specialists/, responses, dispatch
src/graphs/   core.py
src/tools/    shared capabilities (research — planned)
src/models/   state.py
prompts/      system/, cursor/, resets/, grok-build/
docs/         architecture.md, plans/
```

---

*Update this file when a new plan doc becomes mandatory reading (e.g. after specialist-research Phase 1 is approved, keep it in Tier 2).*
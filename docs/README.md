# Documentation

This directory contains the main human-facing documentation for the Mycelium project.

## Primary Documents

- **[architecture.md](architecture.md)** — The current architecture and implementation direction. This is the active source of truth for how the system is designed and built in the current phase.
- **[vision.md](vision.md)** — Historical high-level project vision (deprecated).

## Foundational Principles

The core rules, philosophy, and collaboration model live in:

- `prompts/system/CORE_PROMPT.md` — The canonical project brief. This is the primary document for AI agents (Grok, Cursor, etc.) working on the project.

## Workflow & Agent Handoffs

Detailed information about how we direct Cursor agents lives in:

- `prompts/cursor/WORKFLOW.md`
- `prompts/cursor/README.md`

## Design plans (`plans/`)

Topic-specific plans and backlogs. Start with [architecture.md](architecture.md); use these for depth.

| Topic | Document |
|-------|----------|
| Specialist research (Phase 1) | [plans/specialist-research-phase1.md](plans/specialist-research-phase1.md) |
| **Research prompt context** (MVR bind disambiguation + peer specialists, June 2026) | Slices `2010` / `2110` in `prompts/cursor/done/`; implementation in `src/tools/research.py`, templates under `src/agents/factory/templates/research/` |
| Research robustness backlog (post-2010) | [plans/research-robustness-backlog.md](plans/research-robustness-backlog.md) |
| Entity protocol program | [plans/entity-protocol-and-registry-program.md](plans/entity-protocol-and-registry-program.md) |
| Networks / multi-network | [plans/networks-terminology.md](plans/networks-terminology.md), [plans/networks-phase5.md](plans/networks-phase5.md) |

### Research prompts (June 2026)

On cache miss, `build_research_prompts()` assembles the LLM user message:

1. **MVR bind disambiguation** — `network.json` → `MvrPolicy.bind_fields`; non-name bind values must appear in the first `web_search` when present (CRM default: `employer`).
2. **Peer specialist findings** — read-only slices from other categories for the same `entity_id` (contact email, demographic city, etc.), rendered above the JSON payload.
3. **Category fragment** — per-category guidance from `templates/research/<category>.md.j2`.

Templates load at runtime (no specialist regen for prompt-only changes). Network specialists must be regenerated from `specialist_agent.py.j2` when `_research_context()` changes. See [research-robustness-backlog.md](plans/research-robustness-backlog.md) for follow-on hardening ideas.

## Other Notes

- `TODO.md` (in the project root) tracks long-term tasks and decisions between Paul and Grok.
- **Paul + Grok design conversations** (full context beyond TODO bullets): [`plans/conversations/`](plans/conversations/README.md)
- Historical task artifacts from the Cursor prompting system are stored in `prompts/cursor/done/`.

---

**Note:** As of June 2026, documentation was consolidated. See `architecture.md` for the current state of the project.
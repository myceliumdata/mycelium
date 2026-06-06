# Mycelium — TODO

Open tasks and roadmap. **Source of truth for architecture:** `docs/architecture.md`.  
**Implementation handoffs:** `prompts/cursor/next/` per `prompts/cursor/WORKFLOW.md`.

---

## Top priority — Brand & launch

- [ ] **Explainer video** — short intro to Mycelium networks (specialists, query flow, vision). For site, repo, outreach.
- [ ] **Logo** — mark for myceliumdata.org, GitHub org, docs, video. Decision owner: Paul.

## Near term — Engineering

- [ ] **MCP singleton reload** — reload registry / category tree / graph state per `query_person` so MCP matches CLI without manual server restart (Paul hit this with email vs CLI).
- [ ] **End-to-end LangSmith verification** — `.env`, CLI/MCP smoke with tracing on in Paul's environment.
- [ ] **GitHub Actions (non-blocking)** — ruff + pytest workflows; optional/manual until core stabilizes (per May 2026 note).
- [ ] **README refresh** — run instructions, MCP `cwd` + `requested_attributes` example, architecture pointer.

## Hosting & governance

- [ ] **GitHub org + repo move** — create org (myceliumdata.org alignment), transfer `mycelium` from `murphy/mycelium`, make **public**.
- [ ] **Branch protection** — require Paul's approval on PRs to `main` (CODEOWNERS + branch rules).
- [x] **MIT license** — `LICENSE` at repo root (June 2026).

## Product vision — Networks (roadmap)

Plan in `docs/plans/` before Cursor slices.

### Terminology & bootstrap

- [ ] Rename “instance” → **network** in docs and user-facing language.
- [ ] **Network creation prompt** → ontology of specialist agents (not fixed six-category default).
- [ ] **Custom specialists** per network.

### Protocol & conversation

- [ ] **Inter-network discovery and handoff** (e.g. car network → airplane network).
- [ ] **Long-running threads** — suspend and ask client for clarification (`thread_id` + checkpoints; bones exist).
- [ ] **Query-as-seed** — unknown people created from queries; disambiguate before research (e.g. generic “Paul Murphy” + address).

## Future / deferred

- [ ] **Data addition (internal)** — design coordination for new core records without public `provided_data`; persist via specialists; validation and status taxonomy.
- [ ] **Response builders** — optional refactor of `assemble_response` / specialist-specific message shaping.
- [ ] **MCP packaging** — keep in-repo vs extract later.
- [ ] **CoreStorage DI** — evaluate dependency injection when multiple agents share storage.
- [ ] **Release / versioning** strategy.
- [ ] **Process** — refine `WORKFLOW.md`, `prompts/cursor/done/` retention, status tooling.

## Done (archive)

Major landed work (no action):

- Seed-data-context redesign (`data/seed.json`, graph: supervisor → build_context → invoke_specialists → assemble_response; no `core_data`).
- Phase 1 sync specialist research (LLM + Tavily, slices 1100–1400).
- Query-only public API (CLI/MCP `PersonQuery`).
- Classification engine + Agent Factory + dynamic dispatch.
- Runtime data gitignored (`data/agents/`, registry, generated `*_specialist.py`, `categories.json`).
- `PersonResponse`: `results`, `message`, `debug`, `trace_id`, `thread_id`.
- Smoke/full test split; initial CRM seed (`data/seed_crm.json` → `data/seed.json`).
- Pre-redesign cleanup (derivative datasets, orchestrator→supervisor, ingestion handshake removed).

**Cancelled (obsolete after redesign):**

- ~~`routing.py` / `core_data_agent` follow-ups~~ — `core_data` removed; routing lives in supervisor + `dispatch.py` + graph nodes.

---

Last updated: 2026-06-04 (TODO cleanup; org move in progress)
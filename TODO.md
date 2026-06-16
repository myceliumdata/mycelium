# Mycelium — TODO

Open tasks and roadmap (**Grok + Paul only** — Cursor reads for context, does not edit; see `prompts/cursor/WORKFLOW.md`).  
**New contributors:** [`docs/onboarding.md`](docs/onboarding.md). **Architecture:** [`docs/architecture.md`](docs/architecture.md).  
**Cursor queue:** `prompts/cursor/next/`. **Website:** `../mycelium-website/prompts/cursor/next/`.

**Shipped history:** `docs/plans/`, `prompts/cursor/done/`, git log.

---

## Next up (Paul)

- [ ] **Profiling — Lahman bootstrap / storage hot paths** — After **timing test 6** (`c5e5bce` incremental specialist writes), profile `refresh-example-network baseball` bind loop if wall-clock still surprises. Goal: confirm incremental upsert dominates; quantify remaining costs (`add_bind_alias` + `_rebuild_field_indexes`, `write_bind_fields_multi`, SQLite). Tools: `time -p`, `cProfile` / `py-spy` on `LahmanSeedHandler` + `write_fields` path; record in [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md). Prior post-mortem: [`docs/plans/storage-evolution-program.md`](docs/plans/storage-evolution-program.md) § Post-mortem.
- [ ] **Storage evolution timing test 6** — Fresh `--root`; `time -p ./bin/refresh-example-network baseball --yes --no-default`; record **real** in timing-gates doc Test 6 row. Kill any pre-incremental test 5 run first.
- [ ] **`baseball` example network** — Lahman second example; [`docs/plans/baseball-example-program.md`](docs/plans/baseball-example-program.md) (ur: [`mycelium_lahman_design_prompt.md`](docs/plans/mycelium_lahman_design_prompt.md)). Two registry grains (**player** + fan-facing **team** city+name; franchise via specialist), agent-managed warehouse + derivations. **Locked:** uuid4 on load; Lahman `playerID` = source metadata only. **Player MVR (draft):** name + team — team disambiguates homonyms; any team the player played for → same uuid (index TBD). **Seed data:** Paul has `~/mycelium-networks/baseball/seed/lahman_1871-2025_csv.zip` (~40MB); hosting TBD — avoid git blob if possible; SABR Box not bot-fetchable; may self-host URL + ingest script.
  - **Storage evolution:** code slices complete; test 6 + profiling gate demo readiness.
  - **Cursor queue:** query orchestrator grain selection (`target_resolve`, supervisor) — next slice to queue.
  - **LahmanSeedHandler** shipped slice `1700` (committed). Improvised spike in `git stash` (`cursor-improvised lahman seed handler`) — compare optional; drop when done.

### Shipped (2026-06-14)

- [x] **Program 3 — Entity protocol legacy cleanup** — Gate **CLEAR**; tag `program_3`; polish **1560** (P1–P4 `require_full_bind_values`, fail-loud load). Slices 1500–1555 + 1560 + admin poll fix (1555). [`docs/manual-checks/2026-06-14-program3-post-program-gate.md`](docs/manual-checks/2026-06-14-program3-post-program-gate.md).

---

## OSS collaboration (Paul + Grok)

External contributors should not be forced into the Grok + Cursor handoff. Open decisions:

- [ ] **CONTRIBUTING.md** — Ignore `prompts/cursor/`; normal PRs; `./bin/ci-local` sufficient.
- [ ] **Soften always-on Cursor rule** — `alwaysApply: false` on `04-cursor-workflow.mdc`, or move maintainer rules out of public tree.
- [ ] **Gitignore local Cursor config** — `.cursor/permissions.json` at minimum.
- [ ] **Optional: split maintainer ops** — `prompts/cursor/`, `AGENTS.md`, `.cursor/rules/` in private meta repo vs public framework.

**Reference:** `docs/onboarding.md`; `prompts/cursor/README.md` (maintainers only).

---

## Process (Grok + Paul)

- **Archive design sessions** — End substantive Paul + Grok design threads in [`docs/plans/conversations/`](docs/plans/conversations/README.md) (survives chat compacting). Distill locks into program docs when ready.
- **Website review after major pushes** — Review [myceliumdata.org](https://myceliumdata.org) vs `docs/architecture.md` + `docs/onboarding.md`. Queue in **`../mycelium-website/prompts/cursor/next/`**. Paul pushes and deploys.

---

## Admin UI (open)

- [ ] **Admin auth** — localhost-only today; design before remote admin.
- [ ] **Binding context** — full negotiation metadata on `/status`; query panel binding UX.
- [ ] **Edit / correct attribute values** — see **Operator attribute correction** below.
- [ ] **Force re-research** — see **Operator force re-research** below.

---

## Brand

- [ ] **Product motivation / narrative** — Decide what to do with origin stories (not the only “why”): (1) MCP-on-raw-data factory insight — [`docs/plans/conversations/2026-06-14-data-factory-origin.md`](docs/plans/conversations/2026-06-14-data-factory-origin.md); (2) blockchain full-index data volumes (new data every block). Targets TBD: `architecture.md` intro, onboarding, website.
- [ ] **Explainer video** — *de-prioritized*; short networks intro when time allows.

---

## Query, entity & research (open)

- [ ] **Settlement protocol** — Real x402 `PaymentProvider`, fundable-wallet harness, HTTP 402 gateway, rebate/pool ledger. Deferred from metering Slice 11.
- [ ] **Per-record query messages (multi-match)** — Collective `message` today; per-id status when attrs diverge per match.
- [ ] **Multi-turn thread semantics** — Reuse specialist cache across attributes on one `thread_id` without redundant research.
- [ ] **Long-running threads** — Suspend and ask client for clarification (`thread_id` + checkpoints).
- [ ] **Search indices** — Scale partial lookup + secondary indices (email → id, etc.). Design when beyond CRM scale.
- [ ] **Fuzzy match upgrades (aliases & prefixes)** — prefer **LLM alias expansion** with domain context (local LLM; see [`docs/plans/conversations/2026-06-16-llm-alias-resolution.md`](docs/plans/conversations/2026-06-16-llm-alias-resolution.md)) over explicit prefix/alias tables. Policy: [`docs/plans/fuzzy-lookup-policy.md`](docs/plans/fuzzy-lookup-policy.md).
- [ ] **Query / search any field** — Lookup/search on extended attrs, not only MVR/indexed fields; fuzzy on 0-hit. After index story matures.
- [ ] **Operator attribute correction** — Admin (primary): view/edit specialist storage values, operator override provenance, re-research policy.
- [ ] **Operator force re-research** — Explicit retry per entity + attribute; optional operator hints in research context.
- [ ] **Research robustness** — [`docs/plans/research-robustness-backlog.md`](docs/plans/research-robustness-backlog.md): source-quality rules, multi-identity → `na`, `network.json` research policy.
- [ ] **Data attribution (product — USP)** — MCP/`describe_network` surfacing, staleness/re-research policy beyond Slice 8 basics.
- [ ] **Derivative data — token-efficiency examples (USP)** — Once specialists materialize **derivative** attrs (warehouse joins, aggregates, rate stats, etc.), ship **worked examples** that quantify **lower client token cost** when retrieving the derivative via Mycelium vs. fetching/reasoning over all **source** rows the specialist used to build it. Deliverables TBD: side-by-side MCP/query transcripts or scripts (token counts), `examples/networks/` demo query pack, website narrative. Natural first host: **baseball** Lahman derivations ([`docs/plans/baseball-example-program.md`](docs/plans/baseball-example-program.md)). Depends on specialist-owned derivative storage + query path to read it.
- [ ] **Seed export (`export-growth-seed`)** — Validated `entities.json` → `seed.json` fragment.
- [ ] **Seed vs grown entity linking** — Network-type-specific merge/override rules.

---

## Future / deferred

- [ ] **Toolbox** — TBD.
- [ ] **Agent tools review** — Catalog tools by domain; framework vs per-network packs; factory binding.
- [ ] **Per-network LangSmith projects** — Optional `mycelium-<network>` per root.
- [ ] **Non-person seed schemas** — Generic entity seed beyond `people[]`.
- [ ] **`network regen-ontology`** — Re-run creation prompt on existing root.
- [ ] **Per-network credentials** — vs framework `.env` today.
- [ ] **Distributed network discovery** — Prerequisite for inter-network handoff.
- [ ] **Inter-network handoff** — Cross-network query routing.
- [ ] **Data addition (internal)** — New core records without public `provided_data`.
- [ ] **Response builders** — Refactor `assemble_response` / message shaping.
- [ ] **MCP packaging** — In-repo vs extract.
- [ ] **CoreStorage DI** — When multiple agents share storage.
- [ ] **Release / versioning** strategy.
- [ ] **Process** — `WORKFLOW.md`, `done/` retention, status tooling.

---

Last updated: 2026-06-17 (derivative token-efficiency USP; test 6 + profiling on deck)
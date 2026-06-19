# Mycelium — TODO

Open tasks and roadmap (**Grok + Paul only** — Cursor reads for context, does not edit; see `prompts/cursor/WORKFLOW.md`).  
**New contributors:** [`docs/onboarding.md`](docs/onboarding.md). **Architecture:** [`docs/architecture.md`](docs/architecture.md).  
**Cursor queue:** `prompts/cursor/next/`. **Website:** `../mycelium-website/prompts/cursor/next/`.

**Shipped history:** `docs/plans/`, `prompts/cursor/done/`, git log.

---

## Next up (Paul)


- [ ] **`bin/smoke-baseball-e2e` — full gate** — Minimal fixture version shipped (`./bin/smoke-baseball-e2e`, ~seconds). Expand to CRM parity: `--full` real Lahman refresh (timing-gate scale, not default CI), team-grain queries after **2100** grain router, lazy-alias scenarios (mock expander), warehouse/derivative queries when ready. See script docstring TODO.
- [ ] **Lahman bootstrap load — keep optimizing (priority)** — Still too slow for demo scale, and **v1 only loads a sliver of Lahman**: warehouse ingests 6 bootstrap tables (~2 s) but `LahmanSeedHandler` only commits **team + player identity binds** (~58k appearance rows → ~24k players) — not batting/pitching derivations, not full 27-table warehouse, not specialist materializations. **Tomorrow:** (1) run **test 6** post-`c5e5bce`; (2) profile remaining hot path; (3) queue slices as needed — likely **`add_bind_alias` without full `_rebuild_field_indexes`**, batch/bootstrap-specific entity paths, bulk specialist bootstrap API, avoid per-row Python loop where SQL batch suffices. Track timings in [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md). Headroom: full Lahman + derivatives will multiply load — identity pass must be **minutes or less** before expanding scope.
- [ ] **Profiling — Lahman bootstrap / storage hot paths** — Part of load optimization above. `time -p`, `cProfile` / `py-spy` on bind loop; record findings in timing-gates doc. See [`docs/plans/storage-evolution-program.md`](docs/plans/storage-evolution-program.md) § Post-mortem.
- [ ] **Storage evolution timing test 6** — Fresh `--root`; `time -p ./bin/refresh-example-network baseball --yes --no-default`; record **real** in timing-gates doc Test 6 row. Kill any pre-incremental test 5 run first.
- [ ] **`baseball` example network** — Lahman second example; [`docs/plans/baseball-example-program.md`](docs/plans/baseball-example-program.md) (ur: [`mycelium_lahman_design_prompt.md`](docs/plans/mycelium_lahman_design_prompt.md)). Two registry grains (**player** + fan-facing **team** city+name; franchise via specialist), agent-managed warehouse + derivations. **Locked:** uuid4 on load; Lahman `playerID` = source metadata only. **Player MVR (draft):** name + team — team disambiguates homonyms; any team the player played for → same uuid (index TBD). **Seed data:** Paul has `~/mycelium-networks/baseball/seed/lahman_1871-2025_csv.zip` (~40MB); hosting TBD — avoid git blob if possible; SABR Box not bot-fetchable; may self-host URL + ingest script.
  - **Storage evolution:** code slices complete; test 6 + profiling gate demo readiness.
  - **Cursor queue:** query orchestrator grain selection (`target_resolve`, supervisor) — next slice to queue.
  - **LahmanSeedHandler** shipped slice `1700` (committed). Improvised spike in `git stash` (`cursor-improvised lahman seed handler`) — compare optional; drop when done.

### Shipped (2026-06-18)

- [x] **Fuzzy bind-field suggestions** — Composite scorer + last-token anchor + first-token prefix; mistake matrix `tests/test_fuzzy_bind_field_suggestion_matrix.py`. Nickname aliases (`Dodgers`) stay LLM path. Slice `2026-06-18-2100-fuzzy-bind-field-suggestion-upgrade`.

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

## Examples & demos (open)

- [ ] **Example network READMEs — standard + gaps** — Coverage today is **uneven**: [`crm/README.md`](examples/networks/crm/README.md) is strong (quick start, admin, growth, layout); [`crm-metering/README.md`](examples/networks/crm-metering/README.md) + [`queries/README.md`](examples/networks/crm-metering/queries/README.md) are adequate; [`empty-crm/README.md`](examples/networks/empty-crm/README.md) and [`baseball/README.md`](examples/networks/baseball/README.md) are thinner (bootstrap-only for baseball; no `examples/networks/README.md` index). **Do:** (1) `examples/networks/README.md` — when to use each network; (2) README checklist (purpose, refresh, step-1/2 queries, MCP fixtures, admin, expected outcomes, links to program doc); (3) bring **empty-crm** + **baseball** up to bar as features land; (4) any new demo (derivative token-efficiency USP) ships with a **solid README** from day one.

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
- [ ] **Field aliases — explore as general framework pattern** — Baseball proved lazy LLM expansion + persisted `field_aliases` on `bootstrap_only` (nicknames with no token overlap, shared ambiguous values across entities). Fuzzy handles typos/prefix; LLM + `guide.md` handles domain shorthand. **Explore generalizing:** manifest policy (e.g. `lazy_field_aliases` vs overloading `bootstrap_only`), step-1 ordering contract across networks, bind_alias vs field_alias roles, suggest-only vs persist-on-resolve, operator visibility/editing, and fit for `query_allowed` networks (CRM acronyms). Distill locks into [`fuzzy-lookup-policy.md`](docs/plans/fuzzy-lookup-policy.md) + alias conversation; implementation tracks CRM deferred item below.
- [ ] **Query / search any field** — Lookup/search on extended attrs, not only MVR/indexed fields; fuzzy on 0-hit. After index story matures.
- [ ] **Operator attribute correction** — Admin (primary): view/edit specialist storage values, operator override provenance, re-research policy.
- [ ] **Operator force re-research** — Explicit retry per entity + attribute; optional operator hints in research context.
- [ ] **Research robustness** — [`docs/plans/research-robustness-backlog.md`](docs/plans/research-robustness-backlog.md): source-quality rules, multi-identity → `na`, `network.json` research policy.
- [ ] **Data attribution (product — USP)** — MCP/`describe_network` surfacing, staleness/re-research policy beyond Slice 8 basics.
- [ ] **Derivative data — token-efficiency examples (USP)** — Once specialists materialize **derivative** attrs (warehouse joins, aggregates, rate stats, etc.), ship **worked examples** that quantify **lower client token cost** when retrieving the derivative via Mycelium vs. fetching/reasoning over all **source** rows the specialist used to build it. Deliverables TBD: side-by-side MCP/query transcripts or scripts (token counts), `examples/networks/` demo query pack, website narrative. Natural first host: **baseball** Lahman derivations ([`docs/plans/baseball-example-program.md`](docs/plans/baseball-example-program.md)). Depends on specialist-owned derivative storage + query path to read it.
- [ ] **MCP `health_check` — generic per-network ping** — Today `ping_query` hardcodes CRM `_HEALTH_PING_LOOKUP` (`name` + `employer`); **baseball** (and any non-CRM network) reports `degraded` even when storage/graph are ok. Replace with grain-aware step-1/2 ping from active `mvr.grains` + a known row per example network (manifest, `guide.md`, or small fixture map). Goal: `ping_query: ok` on CRM and baseball without CRM strings in `src/mycelium_mcp/server.py`.
- [ ] **Computation-centric provenance** — Locked design: every `found` version records **`sources[]`** (input material: dataset pin, web URL, chain state, …) + **`computation`** (actual code that ran — inline or `uri` + `content_hash`) + **`parameters`** (entity `source_keys`, scope). URLs alone are insufficient (web bio, research). Lahman: dataset version + GitHub `retrieved_from`, not table/column in provenance. [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](docs/plans/conversations/2026-06-18-computation-centric-provenance.md). **M1:** warehouse specialist + version writer; extend research path later.
- [x] **Baseball ontology (M1a — before specialists)** — Committed `examples/networks/baseball/categories.json` + `pack_ontology` refresh/bootstrap install (slice `2026-06-19-0900`). Schema-informed categories; CRM stub replaced on baseball roots. Generator deferred.
- [x] **Baseball batting specialist — `career_hr` (M1b)** — Warehouse aggregate + computation provenance; slice `2026-06-19-1000` (committed). Hand-test aggregates after M1c raw gate.
- [x] **Baseball bio specialist — raw `birth_date` (M1c)** — People table read on same provenance contract; slice `2026-06-19-1100` (committed). Hand-test raw before aggregates.
- [ ] **Seed export (`export-growth-seed`)** — Validated `entities.json` → `seed.json` fragment.
- [ ] **Seed vs grown entity linking** — Network-type-specific merge/override rules.

---

## Future / deferred

- [ ] **Dataset manifest** — Network-level catalog of ingested datasets (`id`, `version`, `retrieved_from`, optional `content_hash`) derived from `seed.source.json` + bootstrap. Provenance cites manifest entry by id/version instead of repeating URLs — bloat reduction; not required for provenance M1. [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](docs/plans/conversations/2026-06-18-computation-centric-provenance.md).
- [ ] **Lazy LLM field aliases on open record types (CRM)** — Today alias expansion runs only on `bootstrap_only` (baseball). Extend to `query_allowed` networks after baseball example ships: acronyms / suffix nicknames with no token overlap (`a16z` → `Andreessen Horowitz`, suffix company names) via same `bind_alias_expansion` + `guide.md` pattern — **after fuzzy**, never auto-create. Likely manifest flag (e.g. `lazy_field_aliases`) rather than overloading `bootstrap_only`. Fuzzy keeps typos + first-token prefix; LLM owns domain nicknames. See [`docs/plans/conversations/2026-06-16-llm-alias-resolution.md`](docs/plans/conversations/2026-06-16-llm-alias-resolution.md).
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

Last updated: 2026-06-18 (computation-centric provenance locked; baseball M1 + dataset manifest on TODO)
# Mycelium — TODO

Open tasks and roadmap (**Grok + Paul only** — Cursor reads for context, does not edit; see `prompts/cursor/WORKFLOW.md`).  
**New contributors:** [`docs/onboarding.md`](docs/onboarding.md). **Architecture:** [`docs/architecture.md`](docs/architecture.md).  
**Cursor queue:** `prompts/cursor/next/`. **Website:** `../mycelium-website/prompts/cursor/next/`.

**Shipped history:** `docs/plans/`, `prompts/cursor/done/`, git log.

---

## Next up (Paul)

- [ ] **Review architecture doc + whys** — [`docs/architecture.md`](docs/architecture.md) and [`docs/architecture/whys/`](docs/architecture/whys/README.md) (nine rationale topics; future candidates listed in whys README).

- [ ] **`bin/smoke-baseball-e2e` — full gate** — Minimal fixture version shipped (`./bin/smoke-baseball-e2e`, ~seconds): player + team record-type queries, warehouse stats, mocked derive. **Still open:** `--full` real Lahman refresh (timing-gate scale, not default CI), lazy-alias scenarios (mock expander). See script docstring TODO. *(Live Lahman anchors live in live gate, not smoke.)*
- [ ] **Lahman bootstrap load — keep optimizing (priority)** — Still too slow for demo scale, and **v1 only loads a sliver of Lahman**: warehouse ingests 6 bootstrap tables (~2 s) but `LahmanSeedHandler` only commits **team + player identity binds** (~58k appearance rows → ~24k players) — not batting/pitching derivations, not full 27-table warehouse, not specialist materializations. **Next:** (1) run **test 6** post-`c5e5bce`; (2) profile remaining hot path; (3) queue slices as needed — likely **`add_bind_alias` without full `_rebuild_field_indexes`**, batch/bootstrap-specific entity paths, bulk specialist bootstrap API, avoid per-row Python loop where SQL batch suffices. Track timings in [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md). Headroom: full Lahman + derivatives will multiply load — identity pass must be **minutes or less** before expanding scope.
- [ ] **Profiling — Lahman bootstrap / storage hot paths** — Part of load optimization above. `time -p`, `cProfile` / `py-spy` on bind loop; record findings in timing-gates doc. See [`docs/plans/storage-evolution-program.md`](docs/plans/storage-evolution-program.md) § Post-mortem.
- [ ] **Storage evolution timing test 6** — Fresh `--root`; `time -p ./bin/refresh-example-network baseball --yes --no-default`; record **real** in timing-gates doc Test 6 row. Kill any pre-incremental test 5 run first.
- [ ] **Baseball pack → framework extraction review** — After M14 + program slices land, audit remaining pack code (`warehouse_resolve`, `derive_resolve`, `product_common`, bootstrap handlers) for promotion into `src/`. M14 starts the hierarchy; this pass finishes resolver protocols and product tier. Goal: second warehouse network subclasses framework bases only.
- [ ] **Warehouse stat specialist base class (M14)** — Cursor: `prompts/cursor/next/2026-06-20-2340-baseball-warehouse-stat-specialist-base-class-m14.md`. **After M13 + 2280, before 2350 polish.** Ship **`WarehousePlayerStatSpecialist` / `WarehouseTeamStatSpecialist` in `src/agents/specialists/`** (framework); baseball pack = thin subclasses + resolver hooks. Manifest-driven derive-on-miss. Paul lock: **framework hierarchy**, not pack-only — see [`docs/architecture/whys/specialist-class-hierarchy.md`](docs/architecture/whys/specialist-class-hierarchy.md).
- [ ] **Specialist hierarchy — next tiers** — After M14: `ProductTeamSpecialist` (roster/franchise + scope-aware cache); align factory CRM template with `ResearchSpecialistAgent`; onboarding “subclass framework bases” walkthrough.
- [ ] **Stat specialist model — document** — Largely addressed by specialist-class-hierarchy why; extend onboarding after M14 + product base land.
- [ ] **`baseball` example network** — Lahman second example; full slice map in [`docs/plans/baseball-example-program.md`](docs/plans/baseball-example-program.md). **Not done** when batting+bio pass — need pitching, team_season, fielding, scope, cross-record product specialists, full ingest. **Cursor queue:** `prompts/cursor/next/2026-06-20-22*.md` (M7–M13).
  - **Shipped (identity + batting path):** M1a–M4b, record-type routing, live gate 16/16, MCP `health_ping`, examples index.
  - **Shipped (domain parity M5–M6, 2026-06-20 evening):** `pitching_specialist`, `team_identity_specialist`, `team_season_specialist` pack modules; manifest aliases; multi-domain smoke (`career_hr` + `career_wins`).
  - **Next slices:** M13 full warehouse ingest → 2280 bootstrap perf → **M14 warehouse stat base class** → 2350 polish capstone.
  - **Bootstrap perf:** test 6 + profiling still gates casual demo (orthogonal to specialist coverage).

### Shipped (2026-06-20 afternoon)

- [x] **Live gate afternoon sweep** — All four example networks pass (`./bin/gate-live`): baseball 16/16, crm 8/8, crm-metering 4/4, empty-crm 4/4 (32 scenarios). Manual gate: [`docs/manual-checks/2026-06-20-live-gate-program.md`](docs/manual-checks/2026-06-20-live-gate-program.md).
- [x] **Warm-cache intent inference removed** — `infer_slug_from_warm_cache` dropped; fixes `ops` derive bleeding `career_avg` cache. Commit `588de57`; review `2026-06-20-1950`.
- [x] **CLI delivery network hints** — Step-1 stderr hint + cross-network step-2 messages. Commit `df770a9`; review `2026-06-20-2000`.
- [x] **gate-live fresh-derive default** — Baseball derive cache auto-clears; CRM networks auto-refresh (`--no-fresh-derive` / `--no-refresh` opt-out). Commit `24abc9e`; review `2026-06-20-1995`.
- [x] **crm-metering live gate fix** — Quote-on-step-1 scenario + README auto-refresh notes. Commit `57ab808`.
- [x] **Docs sweep** — Onboarding, live gate program, design conversation archive. Commits `f1a9477`, `7c9d1e2`.
- [x] **MCP `health_check` per-network ping** — `health_ping.lookup` in `network.json`; no CRM hardcode in `server.py`. CRM + baseball examples configured; empty-crm skips ping until growth.
- [x] **Example networks index** — [`examples/networks/README.md`](examples/networks/README.md); baseball README query examples + gate notes.

### Shipped (2026-06-20)

- [x] **Live gate regression (example networks)** — Opt-in **`./bin/gate-live <network>`** (`baseball`, `crm`, `crm-metering`, `empty-crm`): real `~/mycelium-networks/<network>` + `.env`, per-network YAML catalogs, `@pytest.mark.live_gate` (**never CI**). Commit `fe23f9f`; slice `2026-06-20-1600-live-gate-baseball-crm`. Manual gate: [`docs/manual-checks/2026-06-20-live-gate-program.md`](docs/manual-checks/2026-06-20-live-gate-program.md). Design: [`docs/plans/conversations/2026-06-20-live-gate-program.md`](docs/plans/conversations/2026-06-20-live-gate-program.md).
- [x] **Baseball warehouse derive M-track polish** — Intent LLM skip on warm cache (later reverted for map-miss safety), legacy alias read across labels, smoke `intent_dedup_mocked`. Commits `2be1b0e`, `b3ed225`; slice `2026-06-20-1500-baseball-warehouse-derive-m-polish`.

### Shipped (2026-06-18)

- [x] **Fuzzy bind-field suggestions** — Composite scorer + last-token anchor + first-token prefix; mistake matrix `tests/test_fuzzy_bind_field_suggestion_matrix.py`. Nickname aliases (`Dodgers`) stay LLM path. Slice `2026-06-18-2100-fuzzy-bind-field-suggestion-upgrade`.

### Shipped (2026-06-14)

- [x] **Program 3 — Entity protocol legacy cleanup** — Gate **CLEAR**; tag `program_3`; polish **1560** (P1–P4 `require_full_bind_values`, fail-loud load). Slices 1500–1555 + 1560 + admin poll fix (1555). [`docs/manual-checks/2026-06-14-program3-post-program-gate.md`](docs/manual-checks/2026-06-14-program3-post-program-gate.md).

---

## OSS collaboration (Paul + Grok)

External contributors should not be forced into the Grok + Cursor handoff. Open decisions:

- [ ] **Contributor walkthroughs** — End-to-end examples for new contributors: curated query list (CLI, MCP/chat) with **expected response shape** and **which framework or project feature each query demonstrates** (two-step delivery, record-type routing, warehouse manifest, derive, provenance, multi-specialist merge, etc.). Host in `docs/onboarding.md` or a dedicated `docs/contributor-walkthrough.md`; cross-link from `examples/networks/README.md`.
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

- [ ] **Public baseball example (feedback loop)** — Ship a **public** Lahman demo (website or standalone) so outsiders can try queries and give feedback. Open design: embedded chat vs MCP-only, hosted network root vs read-only snapshot, rate limits, cost model. Depends on bootstrap perf (`2280`) and program slices M10–M13 for credible coverage. Track alongside [`docs/plans/baseball-example-program.md`](docs/plans/baseball-example-program.md).
- [ ] **Example network READMEs — remaining gaps** — Index shipped ([`examples/networks/README.md`](examples/networks/README.md)). **Still thin:** [`empty-crm/README.md`](examples/networks/empty-crm/README.md) vs CRM bar; thicken as features land. Any new demo (derivative token-efficiency USP) ships with a **solid README** from day one.

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

- [ ] **MCP usage economics (Claude & other hosts)** — Research how external chat clients (Claude, ChatGPT, etc.) can **pay for MCP tool usage** — operator-funded vs end-user wallet, per-network metering hooks, settlement protocol tie-in, hosted demo cost recovery. Output: short design note + whether Mycelium exposes usage quotes on MCP `health_check` / tool metadata. Related: **Settlement protocol** below.
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
- [ ] **Computation-centric provenance** — Locked design: every `found` version records **`sources[]`** (input material: dataset pin, web URL, chain state, …) + **`computation`** (actual code that ran — inline or `uri` + `content_hash`) + **`parameters`** (**all** runtime input values — entity `source_keys`, `warehouse` path, scope, etc. — even when `computation` is a URI). URLs alone are insufficient (web bio, research). Lahman: dataset version + GitHub `retrieved_from`, not table/column in provenance. [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](docs/plans/conversations/2026-06-18-computation-centric-provenance.md). **M1 shipped** (warehouse specialists + version writer); **follow-up:** full `parameters` (e.g. `warehouse`), research-path migration.
- [ ] **Deep provenance (request-time lineage expansion)** — Shallow `provenance: true` ships computation envelope only; clients need opt-in **input-fact lineage** (warehouse rows, per-season aggregates, research snippets). Flag TBD on step 1; response shape TBD (`inputs[]` vs lazy expand). Guinea pig: Aaron `career_avg` / `career_hr`. [`docs/plans/conversations/2026-06-19-deep-provenance-lineage-expansion.md`](docs/plans/conversations/2026-06-19-deep-provenance-lineage-expansion.md).
- [ ] **Specialist derivative retention (agent-managed storage)** — **Now:** always cache computed `found` versions on deliver (current behavior). **Future:** each specialist manages its own storage economically — weigh **storage cost vs recompute cost** (needs metering/cost signals); **access patterns over time** decide keep vs evict even when recomputation is cheap. Humans should not tune this; agents can with cost data. Origin: [`docs/plans/conversations/2026-06-14-data-factory-origin.md`](docs/plans/conversations/2026-06-14-data-factory-origin.md) § derivative retention.
- [x] **Baseball ontology (M1a — before specialists)** — Committed `examples/networks/baseball/categories.json` + `pack_ontology` refresh/bootstrap install (slice `2026-06-19-0900`). Schema-informed categories; CRM stub replaced on baseball roots. Generator deferred.
- [x] **Baseball batting specialist — `career_hr` (M1b)** — Warehouse aggregate + computation provenance; slice `2026-06-19-1000` (committed). Hand-test aggregates after M1c raw gate.
- [x] **Baseball bio specialist — raw `birth_date` (M1c)** — People table read on same provenance contract; slice `2026-06-19-1100` (committed). Hand-test raw before aggregates.
- [x] **Baseball warehouse manifest (M2a)** — Bootstrap/sync introspects `lahman.sqlite` → `warehouse_manifest.json` (tables, columns, grain, domain→specialist); surface in `describe_network`. Unlock layer 3 without enumerating every stat in `attribute_map`. Prompt `2026-06-19-1400-baseball-warehouse-manifest-m2a`. Polish nits → `2026-06-19-1700-baseball-warehouse-manifest-m2a-polish` (after M2c). Conversation [`2026-06-19-warehouse-factory-layer3-specialist-emergence.md`](docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md).
- [x] **Baseball generic warehouse resolver (M2b)** — Manifest conventions (`career_sum`, raw People columns) in `batting_specialist` / `bio_specialist`; `career_rbi`, `career_hits`, etc. without per-attr `if` branches. Polish nits → `2026-06-19-1700-baseball-warehouse-manifest-m2a-polish` (after M2c).
- [x] **Baseball identity bind on deliver (M2c)** — `debut_team` / `debut_year` from registry bind via `player_identity_specialist`; warehouse `parameters` complete from M2b. Hand-test gate passed on live Lahman (June 2026).
- [x] **Baseball M2 polish** — Manifest capabilities dedup, MCP blurb, `specialist_loader`, full `parameters`, multi-attr test/smoke, hand-test doc M2 extended gate. Prompt `2026-06-19-1700-baseball-warehouse-manifest-m2a-polish`.
- [x] **Baseball derive codegen sandbox (M3)** — `derive_sandbox` + pack `derive_resolve`; `derive_candidates: ["career_avg"]`; mocked LLM e2e + provenance. Commit `35a89ab`. Review `2026-06-19-1800-baseball-derive-codegen-sandbox-m3`.
- [x] **Baseball derive retry on error (M3b)** — Up to 5 attempts; fix prompt with execution error + failed source; `sqlite3.Error` → `N/A` not MCP error. Review `2026-06-19-1900-baseball-derive-retry-on-error-m3b`. Manual Lahman `career_avg` gate for Paul.
- [x] **Baseball derive context + semantic review (M3c)** — Manifest context on all derive/fix/review prompts; LLM review before cache; tag `first_llm_computed_result`. Review `2026-06-19-2100-baseball-derive-context-semantic-review-m3c`. Aaron `career_avg` ≈ 0.305 live.
- [x] **Baseball free-form derive (M4)** — `derive_on_miss` on batting domain; any manifest miss → M3c pipeline (removed `derive_candidates` whitelist). Guinea pig: `ops`. Review `2026-06-19-2200-baseball-free-form-derive-m4`.
- [x] **Baseball derive label normalization (M4b)** — LLM **intent slug** before cache lookup: synonym labels → one canonical storage key. Split **`MYCELIUM_INTENT_NORMALIZATION_MODEL`** vs **`MYCELIUM_COMPUTATION_CODEGEN_MODEL`**; `intent_map.json` per network root; provenance `attribute` + `intent_slug`; storage under slug, deliver requested label. Commit `5fdf865`; manual gate [`docs/manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md`](docs/manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md) **CLEAR** (Aaron `career_avg` → `batting_average`, no second codegen). Design: [`docs/plans/conversations/2026-06-20-baseball-m4b-intent-normalization.md`](docs/plans/conversations/2026-06-20-baseball-m4b-intent-normalization.md). **Warehouse derive M track complete** — NL `question` deferred unlikely: [`docs/plans/unlikely/README.md`](docs/plans/unlikely/README.md). Polish shipped 2026-06-20 (see Shipped section).
- [x] **Record-type query routing (baseball + CRM)** — Lookup-key inference in `network/mvr.py`; slices 1100/1800; live gate + `bin/smoke-baseball-e2e` team scenarios. Design: [`docs/query-record-type-router.md`](docs/query-record-type-router.md).

- [ ] **Specialist promotion (derive → product specialist)** — **Out of scope for automation now.** Future: derive telemetry + compute/storage cost signals → agent recommends promoting repeat cross-domain computations to new category + pack specialist; Paul/Grok approve slices until automated. Suppress factory research stub for warehouse categories on baseball. [`2026-06-19-warehouse-factory-layer3-specialist-emergence.md`](docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md).
- [ ] **Seed export (`export-growth-seed`)** — Validated `entities.json` → `seed.json` fragment.
- [ ] **Seed vs grown entity linking** — Network-type-specific merge/override rules.

---

## Future / deferred

- [x] **LLM model configuration — env-only (v1 partial)** — Shipped `src/utils/llm_models.py` + five `MYCELIUM_*_MODEL` accessors (`MYCELIUM_COMPUTATION_CODEGEN_MODEL`, classification, ontology, research, alias expansion); remediation slice renames derive → computation codegen. **Insufficient** — still falls back to hardcoded `gpt-4o-mini` when unset; no provider dimension. See **LLM model configuration — strict (review)** below.
- [ ] **LLM model configuration — strict (review)** — **Review and redesign** v1 model env (slices `2026-06-19-2330`, `2026-06-20-0900`). Paul lock: **no guessing** — operator must explicitly configure **provider + model** for each production LLM subsystem (**six vars at minimum** once M4b ships: add `MYCELIUM_INTENT_NORMALIZATION_MODEL` to the existing five). **Missing required var = hard failure at startup** (CLI, MCP `_bootstrap`, admin daemon) — not silent fallback to a baked-in default. Drop `FALLBACK_MODEL` / unset-means-mini behavior. Open design: env shape (e.g. `openai:gpt-4o` per var vs paired `MYCELIUM_*_PROVIDER` + `MYCELIUM_*_MODEL`), whether agent-factory refine is required or opt-in, validation error messages, `.env.example` as explicit template with no implied defaults. Origin: computation codegen needs `gpt-4o`; unset vars hiding misconfiguration is unacceptable for a critical framework capability.
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

Last updated: 2026-06-21 (specialist-class-hierarchy why; M14 = framework bases in src/)
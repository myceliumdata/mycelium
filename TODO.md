# Mycelium — TODO

Open tasks and roadmap (**Grok + Paul only** — Cursor reads for context, does not edit; see `prompts/cursor/WORKFLOW.md`).  
**New contributors:** start at [`docs/onboarding.md`](docs/onboarding.md).  
**Architecture:** [`docs/architecture.md`](docs/architecture.md).  
**Framework Cursor handoffs:** `prompts/cursor/next/`. **Website handoffs:** sibling repo `mycelium-website/prompts/cursor/next/`.

---

## Next up (Paul — June 2026)

**Priority order:**

0. [x] **Provisional validation on step-2 deliver** — [`1400`](prompts/cursor/done/2026-06-14-1400-provisional-validation-step2-deliver/) **Approved** — Paul manual validation test before `1410`.
1. [ ] **Multi-match step-2 deliver truncation** — Cursor [`1410`](prompts/cursor/next/2026-06-14-1410-multi-match-step2-deliver-truncation.md). After Paul confirms `1400` on live/MCP.
2. [ ] **Program 2 manual gate (fresh from scratch)** — Follow [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](docs/manual-checks/2026-06-13-program2-post-program-gate.md) (rewritten June 2026 after seed-refresh, empty-crm MVR, and capstone-test fixes). Re-run after validation fix if Wrong Corp / multi-match paths are in scope. Branch is **~38 commits ahead** of `origin/main` (run `git log origin/main..HEAD --oneline | wc -l` before testing); do not push until gate **CLEAR**.
3. [x] **Hands-on: `empty-crm` example** — verified June 2026 (refresh → no seed/entities → Paul Murphy bind → 1 validated row; `network status` Entities ✅). Nit fixed: `network_metadata` no longer lets `MYCELIUM_NETWORK` override explicit `--network-dir`. **Re-verify** as part of gate Check 4b (MVR bootstrap fix landed after this checkbox).
4. [x] **Historical assumptions review** — Phase 1: [`docs/plans/historical-assumptions-audit.md`](docs/plans/historical-assumptions-audit.md). Phase 2 done: legacy ingest + SQLite `people` removed — [`2026-06-10-legacy-ingest-storage-removal`](prompts/cursor/done/2026-06-10-legacy-ingest-storage-removal/); memory in [`docs/legacy-ingest-and-storage-reference.md`](docs/legacy-ingest-and-storage-reference.md).
5. [x] **Identity vocabulary rename (breaking)** — Done (`538867e`). Reviews: [`rename`](prompts/cursor/done/2026-06-10-entity-identity-vocabulary-rename/review.md), [`fix`](prompts/cursor/done/2026-06-10-entity-identity-vocabulary-rename-fix/review.md).
6. [x] **Network create optional `--seed`** — Done (reviewed, 305 tests). Review: [`network-create-optional-seed`](prompts/cursor/done/2026-06-10-network-create-optional-seed/review.md).
7. [x] **Project website copy** — Done (`../mycelium-website`, June 2026). Option A overhaul + copy pass deployed by Paul.
8. [x] **Contributor doc hygiene (P1)** — [`docs/onboarding.md`](docs/onboarding.md); audit Phase 2 closed; website copy pass done in **mycelium-website** (`cd7e796`).

---

## OSS collaboration with AI agents (Paul + Grok — design backlog)

**Problem:** This repo ships maintainer-specific multi-agent workflow (`prompts/cursor/`, `AGENTS.md`, `.cursor/rules/`) alongside normal framework code. External contributors should not be forced into Paul’s Grok + Cursor handoff.

**Conversation summary (June 2026):**

| Artifact | Imposes on OSS contributors? | Notes |
|----------|------------------------------|-------|
| `prompts/cursor/WORKFLOW.md` + `done/*/prompt.md` + `output.md` + `review.md` | **No** (passive) | Audit trail of how features were built; optional unless you use the queue. `prompt.md`/`output.md` are Cursor deliverables per slice; Grok adds `review.md`. |
| `AGENTS.md` | **No** | Grok Build only — irrelevant to normal git/PR workflow. |
| `.cursor/rules/04-cursor-workflow.mdc` (`alwaysApply: true`) | **Yes, if using Cursor IDE** | Auto-injects “work on the next task”, no-commit-before-review, etc. Main OSS friction point. |
| `.cursor/permissions.json`, hooks | **Local / optional** | Personal machine config — **do not commit**. |

**Decisions to make (not yet implemented):**

- [ ] **CONTRIBUTING.md clarity** — External contributors: ignore `prompts/cursor/`; open PRs normally; `./bin/ci-local` + smoke tests sufficient.
- [ ] **Soften or remove always-on Cursor rule** — e.g. `alwaysApply: false` on `04-cursor-workflow.mdc`, or move maintainer rules out of public tree.
- [ ] **Gitignore local Cursor config** — `.cursor/permissions.json` at minimum.
- [ ] **Optional: split maintainer ops** — `prompts/cursor/`, `AGENTS.md`, `.cursor/rules/` in private meta repo vs public framework (history vs enforcement).
- [ ] **Example tree policy (done)** — Runtime files (`entities.json`, `deliveries.json`, `agents/`, etc.) must **not** exist under `examples/networks/`; enforced by layout tests, not gitignore (stray files stay visible in `git status`).

**Reference:** `docs/onboarding.md` for human contributors; `prompts/cursor/README.md` for maintainer agent handoffs only.

---

## Process (Grok + Paul)

- **Website review after major pushes** — Whenever a significant framework chunk lands, review [myceliumdata.org](https://myceliumdata.org) against `docs/architecture.md` and `docs/onboarding.md`. Queue work in **`../mycelium-website/prompts/cursor/next/`** (not this repo). **Paul pushes and deploys** the public website repo; Grok/Cursor do not.

---

## Demo (phase)

Operator tooling for Paul’s demos (and future remote admin). **Slices 1 → 4 → 5 → 1200 + admin UI polish (v1–v3) + `restart-admin`: done** (June 2026). **MCP onboarding slices 1–4 done** (June 2026).

### Slice 1 — `refresh-example-network` — **done** (`2026-06-08-1000`)

- [x] **`bin/refresh-example-network <name>`** — shared logic in `src/network/example.py`; wipe + recopy; `--root`, `--register`, `--default`/`--no-default`, `--yes`, `--dry-run`.
- [x] **Removed `bin/copy-example-network`** — README, `examples/networks/crm/README`, integration tests updated.
- [x] **Retired legacy `data/` shim** — `resolve_network_root()` fails loud when unconfigured.
- [x] **`runtime_path()` hardening** — no `data/...` fallbacks; Studio bootstrap via `shell_export_network_paths()` (`a57804d`, `2026-06-08-2400`).
- [x] **Demo runbook** (README) — refresh before demos; restart MCP; fresh `thread_id` per attribute.

### Slice 2 — network status (CLI) — **done** (`2026-06-08-1100`)

- [x] **`mycelium network status`** — `src/network/introspection.py`; entities, ontology, specialists, storage stats; `--json`, `--category`, `--entity`.
- [x] **Tests** — `tests/test_network_status.py` (empty + populated + JSON CLI + person drill-down).

### Slice 3 — admin daemon — **done** (`2026-06-08-1700`)

- [x] **`mycelium-admin` (`uv run mycelium-admin`)** — long-lived **HTTP** admin API on localhost (one process per network, like MCP). env: `MYCELIUM_NETWORK` / `MYCELIUM_NETWORK_ROOT`; default `127.0.0.1:8741`.
  - **v0 read-only:** `GET /health`, `GET /status` (mirrors `network status --json`), `GET /capabilities` via `src/network/introspection.py`.
  - **Later write ops:** refresh, register (slice 4+); remote + auth deferred.

### Slice 4 — admin UI — **done** (`2026-06-08-1800`)

- [x] **`mycelium-admin-ui`** (`admin-ui/`) — Vite + React SPA against admin daemon. Drill-down: network → specialists → entity → fields. Dev: `npm run dev`; demo: build + serve from `mycelium-admin`.
  - Local demos first; same API supports future remote deployments.

### Admin UI polish — **done** (`2026-06-08-2000`, `3b36a4e`)

- [x] **Scannable overview** — ✅/❌ Seed, Ontology, Specialists *(historical UI labels; "Seed" = bootstrap fixture count, not runtime seed loader)*; ontology in guide card; collapsed secondary panels; 3s silent `/status` poll.

### `bin/restart-admin` — **done** (`2026-06-08-2100`, `df32d09`)

- [x] **Dev stack restart** — `./bin/restart-admin`; kill :8741 + :5173; background daemon + foreground Vite; `--demo` optional.

### Admin UI polish v2 — **done** (`2026-06-08-2200`, `c025558`)

- [x] **Categories rename** — Overview + guide inner summary; card title unchanged.
- [x] **Collapse guide card** — outer `<details>` like Entity lookup.
- [x] **Unified disclosure arrows** — `.disclosure-summary` on all summaries.
- [x] **Specialist expand fix** — uncontrolled `<details>`; `fetchJson` HTML guard.

### Admin UI polish v3 — **done** (`2026-06-08-2300`, `7097142`)

- [x] **Remove Refresh button** — 3s poll + visibility refresh replace manual reload.
- [x] **Remove `network_root` line** — debug path not shown in default UI.
- [x] **Capabilities without Refresh** — refetch on tab visible + when `ontology_present` flips false→true.

### Admin UI v2 — entity protocol surfaces (deferred — Paul + Grok)

Backend shipped in entity protocol Slices 1–8; operator-facing admin work deferred while protocol landed. Former backlog: `docs/plans/admin-ui-backlog.md` (cleared June 2026).

**Infrastructure**

- [ ] **Admin auth** — today localhost-only, no credentials; design session/token or operator login before remote admin.
- [x] **Port / bind robustness** — `MYCELIUM_ADMIN_UI_PORT` wired through Vite + `restart-admin` (`2026-06-09`).

**Read-only protocol surfaces** (entity protocol Slices 1–8)

- [x] **Outcome badges** — `POST /query` + Run query panel shows `outcome` badge (`2026-06-09`).
- [x] **Key suggestions** — entity lookup + query panel show `suggestions[]` on near-miss (`2026-06-09`).
- [x] **Required fields** — entity lookup + query panel show `required_fields` on unknown (`2026-06-09`).
- [x] **Registry-backed entities** — status lookup uses `entities.json` registry; match source + validation on drill-down (`2026-06-09`).
- [ ] **Binding context** — query panel accepts optional `binding.employer`; full negotiation metadata on `/status` still open.
- [x] **Validation state** — bind-field status + match `validation_state` on entity drill-down (`2026-06-09`).
- [x] **Research gate indicator** — `research_allowed` on single-match drill-down (`2026-06-09`).
- [x] **Bind vs extended fields** — entity field table separates `bind` vs `extended` rows (`2026-06-09`).
- [x] **Attribution per attribute** — `attr_source` + `last_researched_at` columns when registry row exists (`2026-06-09`).

**Operator write actions** (see also Entity program deferred follow-ups)

- [ ] **Edit / correct attribute values** — entity field drill-down; see **Operator attribute correction**.
- [ ] **Force re-research** — “try again” + optional operator context on entity field drill-down; see **Operator force re-research**.

### Slice 5 — demo polish — **done** (`2026-06-08-1150`)

- [x] **`network status --json` plain stdout** — `jq`-friendly; `test_status_cli_json` parses JSON.
- [x] **Specialists empty-state copy** — ontology-without-storage message.
- [x] **`health_check` bootstrap hint** — `network_configure_hint` in `info` when unconfigured.
- [x] **Refresh `allow_no_default` wiring** — only on `--no-default`; non-`crm` first refresh auto-defaults.
- [x] **Stale plan docs** — `refresh-example-network` in terminology + phase5 plans.

### Status demo format — **done** (`2026-06-08-1200`)

- [x] **Default human output** — `Seed: ✅ (N)`, `Current ontology: ✅/❌` with `category (e.g., a, b, …)`, `Existing specialists: category (count)`; no `Root:`.
- [x] **`--verbose`** — preserves today’s debug layout (agents, modules, status counts).
- [x] **`--person`** — append verbose person block only (demo person UX deferred).

### Hands-on verification — **done** (June 2026)

- [x] **CLI demo runbook** — `refresh-example-network crm`, `network status`, query regression.
- [x] **MCP** — `mycelium-crm` config, `health_check`, `query_entity` (MCP visiting-agent surface queued separately).

---

## Brand & launch

- [x] **Logo** — done (June 2026).
- [ ] **Explainer video** — *de-prioritized*; short intro to networks when time allows (site, repo, outreach).

## Near term — Engineering

- [x] **MCP runtime reload** — `refresh_runtime_from_disk()` before each MCP query (slice `2026-06-09-1200`, `7e991cb`).
- [x] **MCP `health_check` double refresh** — deduped via `_routing_payload` / `_execute_mcp_query` helpers (slice `2026-06-09-0900`).
- [x] **End-to-end LangSmith verification** — CLI + MCP `trace_id`, cloud upload, auto-resolve URLs (June 2026).
- [x] **LangSmith trace URL auto-resolve** — `get_langsmith_trace_url` API resolve + docs (slice `2026-06-09-1000`).
- [x] **GitHub Actions (non-blocking)** — `.github/workflows/ci.yml` (ruff + smoke); not a required merge check yet.
- [x] **README refresh** — run instructions, MCP `cwd` + `requested_attributes`, architecture summary (June 2026).

## Hosting & governance

- [x] **GitHub org + repo move** — [myceliumdata/mycelium](https://github.com/myceliumdata/mycelium) (public; transferred from `murphy/mycelium`, June 2026).
- [x] **Branch protection** — `main` requires PR + CODEOWNERS review (`CODEOWNERS` → `@murphy`). `enforce_admins: false` so Paul can still push to `main` directly while iterating; tighten later if desired.
- [x] **MIT license** — `LICENSE` at repo root (June 2026).

## Product vision — Networks (roadmap)

**Plan:** `docs/plans/networks-terminology.md` + `docs/plans/networks-phase5.md`. **Phase 5 complete** (slices `1500`–`1800`); Paul hands-on verified (June 2026).

### Terminology & bootstrap

- [x] **Networks terminology (Phase 1)** — docs: framework vs network root, default network, MCP-per-network (slice `2026-06-09-1000`).
- [x] **Network path resolver (Phase 2)** — `MYCELIUM_NETWORK_ROOT`, CLI `--network-dir`, legacy `data/` shim (slice `2026-06-09-1100`).
- [x] **Network registry + default (Phase 3)** — `network list|register|use`, config file (slice `2026-06-09-1200`).
- [x] **CRM example network (Phase 4)** — `examples/networks/crm/` in repo (evolving reference); remove flat `data/` seed from default clone (slice `2026-06-09-1300`).
- [x] **Networks integration testing (Phase 4.5)** — `tests/test_network_integration.py` (11 scenarios); MCP path preservation fix in `refresh_runtime_from_disk` (slice `2026-06-09-1400`).
- [x] **Network launch v1 (Phase 5)** — `mycelium network create` (`1500`–`1800`): `--root`, `--seed`, creation `--prompt`, skeleton ontology, `network.json`, registry, MCP snippet; `--dry-run`/`--force`.
- [x] **Custom specialists per network (Phase 5)** — `<network_root>/specialists/` + `MYCELIUM_SPECIALISTS_DIR` (`1500`); factory paths fixed (`1750`).

### Networks polish (short-term — squirt after Phase 4 / Phase 5)

- [x] **Networks polish** — review niggles Phases 2–4 (slice `2026-06-09-1350`): health_check metadata, docs, seed sanitization, example dir runtime cleanup.
- [x] **Categories sample + alignment** — runtime-only `categories.json`; doc sample + polish nits (slice `2026-06-09-1380`).
- [x] **Phase 5 polish** (`2026-06-09-1750`) — test env dedupe; public storage paths + slug helper; ontology API-key skip when `llm=`; create polish; duplicate/>8 ontology tests.
- [x] **Remove reset-mycelium** (`2026-06-09-1760`) — script + tests removed; replacements documented for `1800`.
- [x] **Paul hands-on test (Phase 5)** — CRM `refresh-example-network`, CLI regression, MCP (`mycelium-crm`); June 2026.

### Protocol & conversation — Entity program (Slices 1–8 → Cursor)

**Program index:** [`docs/plans/entity-protocol-and-registry-program.md`](docs/plans/entity-protocol-and-registry-program.md) — **Slices 1–8 + polish shipped**; **Slices 9–12 metering shipped** (June 2026). **Review:** blocking nits → fix slice; non-blocking → [`entity-protocol-polish-post8.md`](docs/plans/entity-protocol-polish-post8.md).

| Slice | Spec | Cursor prompt | Status |
|-------|------|---------------|--------|
| 1 | [`entity-key-suggestions-phase1.md`](docs/plans/entity-key-suggestions-phase1.md) | `1000` + `1005` | **Done** |
| 2 | [`entity-outcome-infrastructure-phase2.md`](docs/plans/entity-outcome-infrastructure-phase2.md) | `1100` | **Done** |
| 2h | — | `1105` smoke test env isolation | **Done** |
| 3 | [`entity-unknown-mvr-phase3.md`](docs/plans/entity-unknown-mvr-phase3.md) | `1200` | **Done** |
| 4 | [`entity-registry-bind-phase4.md`](docs/plans/entity-registry-bind-phase4.md) | `1300` | **Done** |
| 5 | [`entity-validation-phase5.md`](docs/plans/entity-validation-phase5.md) | `1400` | **Done** |
| 6 | [`entity-research-gate-phase6.md`](docs/plans/entity-research-gate-phase6.md) | `1500` | **Done** |
| 7 | [`entity-boundary-cleanup-phase7.md`](docs/plans/entity-boundary-cleanup-phase7.md) | `1600` + `1605` | **Done** |
| 8 | [`entity-growth-phase8.md`](docs/plans/entity-growth-phase8.md) | `1700` | **Done** |
| P | [`entity-protocol-polish-post8.md`](docs/plans/entity-protocol-polish-post8.md) | `1800` | **Done** |

- [x] **Remove `list_specialist_routing` from MCP** — dropped public tool; `_routing_payload()` retained for `health_check` only (`2026-06-08-1400`).
- [x] **MCP onboarding for visiting agents** — **complete** (slices `1300`–`1600`: entity rename, specialist fixup, `guide.md` + `describe_network`, classification-aware messages, polish). Paul MCP live verify done (June 2026).
- [x] **Entity key suggestions (Slice 1 + fix `1005`)** — reviewed and approved (June 2026). Kalman → suggest Kalmans; same-thread retry serde fixed. Context: [`2026-06-08-entity-key-negotiation.md`](docs/plans/conversations/2026-06-08-entity-key-negotiation.md).
- [x] **Entity outcome infrastructure (Slice 2)** — `outcome` on all paths; `response_non_core` → `assembled`; MCP schema + policy (June 2026).
- [x] **Unknown entity + MVR (Slice 3)** — `entity_unknown`, `required_fields`, `network.json` MVR, supervisor short-circuit (June 2026).
- [x] **Entity registry + provisional bind (Slice 4)** — `entities.json`, `EntityQuery.binding`, `resolve_entity`, `entity_bound_provisional` / `entity_under_specified`; duplicate bind → `found` (June 2026).
- [x] **Core validation orchestration (Slice 5)** — `validate_entity` graph node, rule-based MVR checks, `entity_validated`, bind→validate→assembled same turn (June 2026).
- [x] **Research gate (Slice 6)** — `research_gate_allows`, provisional + attrs → `found` + gate message; same-turn validate→research (June 2026).
- [x] **Seed vs specialists boundary (Slice 7 + fix `1605`)** — `entity_id`/`bind` context, `core_identity` deleted, framework specialists regenned (June 2026).
- [x] **Entity growth & attribution (Slice 8)** — registry `attr_sources` + `last_researched_at`; Paul Murphy arc smoke; CRM README growth model (June 2026).
- [x] **Entity protocol polish (post Slice 8, `1800`)** — P1–P14 nits: stronger no-invoke tests, `binding` in `optional_fields`, `planner_context`, research gate defense, `researched_fields` attribution, doc/test fixes (June 2026).
- [x] **Negotiation & metering — Slice 9 design** — Locked June 2026: [`entity-metering-design-phase9.md`](docs/plans/entity-metering-design-phase9.md). Q9a–Q9m incl. Q9i-A (principal optional marginal / required sponsor-pool).
- [x] **Metering negotiation — Slice 10** — Shipped: `quote_required`, stores, gate, 16 tests. Cursor: `prompts/cursor/done/2026-06-09-2100-entity-metering-implementation/`. CRM `metering.enabled: false` default.
- [x] **Metering Slice 10 fix** — Shipped + review approved: [`entity-metering-slice10-fix.md`](docs/plans/entity-metering-slice10-fix.md), `prompts/cursor/done/2026-06-09-2110-entity-metering-slice10-fix/`.
- [x] **Payment settlement — Slice 11** — Shipped + review approved: [`entity-metering-payment-implementation.md`](docs/plans/entity-metering-payment-implementation.md), `prompts/cursor/done/2026-06-09-2200-entity-metering-payment-slice11/`. Negotiation (10) ≠ settlement (11).
- [x] **Metering Slice 11 fix** — Shipped + review approved: [`entity-metering-slice11-fix.md`](docs/plans/entity-metering-slice11-fix.md), `prompts/cursor/done/2026-06-09-2210-entity-metering-payment-slice11-fix/`.
- [x] **Metering negotiation test scaffolding — Slice 12** — Shipped + review approved: [`entity-metering-negotiation-test-scaffolding.md`](docs/plans/entity-metering-negotiation-test-scaffolding.md), `prompts/cursor/done/2026-06-09-2300-entity-metering-negotiation-test-scaffolding/`. `crm-metering` example; CLI + admin + demo script. Paul hands-on verify done (June 2026).
- [x] **Metering Slice 12 fix** — Shipped + review approved: [`entity-metering-slice12-fix.md`](docs/plans/entity-metering-slice12-fix.md), `prompts/cursor/done/2026-06-09-2310-entity-metering-slice12-fix/`. Demo checkpointer, admin docs, subprocess test, MCP queries README.
- [ ] **Settlement protocol** (separate from entity program) — Real x402 `PaymentProvider`, fundable-wallet test harness, HTTP 402 query gateway, rebate/pool ledger, async quotes. Deferred from Slice 11; design backlog when blockchain / anonymous-agent economics land.
- [ ] **Per-record query messages (multi-match)** — v1 keeps collective `message` when `entity_key` matches multiple registry rows (e.g. two Kevin Zhangs); agent disambiguates via `results`. Revisit when non-person or other domains need per-record status in `message` (different attrs per match, async research diverging per id).
- [x] **Thread checkpoint: new query on same `thread_id`** — fixed (`run_query` clears stale `response`; removed `assemble_response` short-circuit; smoke test `test_same_thread_new_query_rebuilds_response`). **Follow-up:** multi-turn merge semantics (reuse specialist cache across attributes on one thread without redundant research) still open.
- [ ] **Long-running threads** — suspend and ask client for clarification (`thread_id` + checkpoints; bones exist).

### Entity program — deferred follow-ups (Paul + Grok)

- [x] **MVR redesign program** — **Complete** (June 2026, pushed). M1–M10 + post-program polish (`create_on_deliver`, admin two-step UX). Plan: [`docs/plans/mvr-redesign-program.md`](docs/plans/mvr-redesign-program.md); gate: [`docs/manual-checks/2026-06-13-mvr-redesign-post-program-gate.md`](docs/manual-checks/2026-06-13-mvr-redesign-post-program-gate.md).
- [x] **Program 1 — Extended attribute provenance** — **Complete** (June 2026). Slices 1–3 + polish `1400` shipped: versioned storage, admin history, `QueryResponse.provenance`. Plan: [`docs/plans/attribute-provenance-program1.md`](docs/plans/attribute-provenance-program1.md). Program 2 (MVR/entity): [`attribute-provenance-and-storage.md`](docs/plans/attribute-provenance-and-storage.md).
- [ ] **Program 2 — MVR bind storage + provenance** — **Committed locally** (Slices 1–3 + polish + remedial fixes + capstone tests). Gate: [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](docs/manual-checks/2026-06-13-program2-post-program-gate.md). Push after **CLEAR**.
- [ ] **Search indices (follow-up)** — MVR redesign v1: per-field indexes on `entities.json` for **partial lookup** (e.g. `employer` → `[ids]`, composite `bind_index` for full MVR match). Maintained atomically on write. **Later:** specialists maintain domain-specific indices (e.g. email → id, linkedin slug → id). Design session when scaling beyond CRM-scale entity counts.
- [ ] **Query / search any field (future)** — Product requirement: clients can query on **any** attribute field, not only MVR/bind/indexed fields. v1 MVR redesign: lookup on indexed MVR subset + UUID identity; this item tracks general-field search (extended attrs, specialist storage scan or secondary indices, optional query restrictions per network). Deferred until after MVR redesign + index story matures.
- [ ] **Operator attribute correction** — Research can return wrong values (e.g. Paul Murphy @ Ormi Labs → LinkedIn `paul-murphy-003360` is not Paul). Operators need to **view and update** extended attributes in specialist storage (LinkedIn, email, etc.): correct value, mark source as operator override, prevent naive re-research from overwriting without policy. Surfaces: admin UI edit on entity field drill-down (primary); optional CLI/MCP operator tool later. **Depends on** attribute provenance design (above). Ties to attribution (`attr_sources` / provenance) and re-research/staleness policy.
- [ ] **Operator force re-research** — Mechanism to **retry** a specialist lookup for a specific entity + attribute (not only edit the stored value). Today retries are automatic for `pending` / `last_error` (env-gated age); operators need an explicit **“try again”** that clears or supersedes a stuck/failed/wrong result and re-invokes research. Optional **operator context** on retry (hint text, known URL, disambiguation notes) passed into the research prompt / `_research_context` so the agent has more to work with. Distinct from attribute correction (manual override) and from naive re-query (same thread may hit cache). Surfaces: admin UI action on entity field drill-down (primary); optional CLI/MCP operator tool. Policy: how hints merge with bind + storage; provenance marks forced retry vs automatic.
- [x] **Research prompt context enrichment** — MVR-driven bind disambiguation + peer `context.specialists` in research prompts. Shipped slice `2026-06-09-2010-research-prompt-context-enrichment` (supersedes employer-hardcoded `2000`).
- [x] **Research peer context prominence** — `PEER SPECIALIST FINDINGS` for flattened `_research_context` shape; human-readable peer block. Shipped slice `2026-06-09-2110-research-peer-context-prominence`.
- [ ] **Research robustness (post-2010)** — Network-agnostic hardening beyond prompts: category source-quality rules, multi-identity conflict → `na`, MVR-generic first-query enforcement, optional `network.json` research policy, audit `first_query`. Design backlog: [`docs/plans/research-robustness-backlog.md`](docs/plans/research-robustness-backlog.md). Angela Murphy–class synthesis failures are explicitly out of scope for `2010` alone.
- [ ] **Data attribution (product — USP)** — core registry fields shipped in Slice 8; follow-on: MCP/`describe_network` surfacing, admin UI (**Attribution per attribute** in Admin UI v2), staleness/re-research policy. Broader provenance story not yet designed.
- [x] **Empty-seed network demo (launch v2)** — `examples/networks/empty-crm/` (seed elimination polish, June 2026). Paul Murphy bind arc via `queries/01-bind-paul-murphy.json`.
- [ ] **Seed export tooling (`export-growth-seed`)** — deferred from Slice 8 (Q8c). Operator script: validated `entities.json` → `seed.json` fragment.
- [ ] **Seed vs grown entity linking** — deferred from Slice 8 (Q8d). Network-type-specific rules (CRM ≠ car parts) before merge/override UX.

### Network launch v2 (design — Paul + Grok)

- [x] **Optional `--seed` on `network create`** — shipped June 2026. [`docs/plans/network-create-optional-seed.md`](docs/plans/network-create-optional-seed.md). `refresh-example-network` auto-bootstraps when example ships `seed.json`.

## Future / deferred

- [ ] **Toolbox** — TBD (Paul + Grok).
- [ ] **Agent tools review** — today specialists get one LangChain tool (`web_search` via Tavily in `src/tools/research.py`); real networks will need dozens (structured lookups, enrichment APIs, calculators, file/DB access, handoffs, etc.). Paul + Grok: catalog required tools by domain, decide framework vs per-network tool packs, registry/discovery pattern, credential boundaries, and how factory-generated specialists bind tools — before scaling ontology/specialist count.
- [ ] **Per-network LangSmith projects (design discussion)** — framework-level `LANGCHAIN_PROJECT` today; optional `mycelium-<network>` per root; wire on `network create` later.
- [ ] **Non-person seed schemas** — v1 `--seed` validates person-shaped `people` array; generic entity seed for vehicles/organisms/artifacts deferred.
- [ ] **`network regen-ontology`** — re-run creation prompt against existing root (structural ontology refresh).
- [ ] **Per-network credentials (design discussion)** — Paul + Grok: keep today’s model (framework `.env` shared across networks) vs per-network API keys, `~/.config/mycelium/credentials`, MCP env templates on `network create`. **Current policy:** framework-level only; documented in README + architecture.
- [ ] **Distributed network discovery** — long-term; networks find each other without shared local config (prerequisite for inter-network handoff). v1 = local `~/.config/mycelium/networks.json` only.
- [ ] **Inter-network handoff** — query routing across networks (e.g. car → airplane); after distributed discovery.
- [ ] **Data addition (internal)** — design coordination for new core records without public `provided_data`; persist via registry + specialists after negotiation. See **Entity registry, validation & growth**.
- [ ] **Response builders** — optional refactor of `assemble_response` / specialist-specific message shaping.
- [ ] **MCP packaging** — keep in-repo vs extract later.
- [ ] **CoreStorage DI** — evaluate dependency injection when multiple agents share storage.
- [ ] **Release / versioning** strategy.
- [ ] **Process** — refine `WORKFLOW.md`, `prompts/cursor/done/` retention, status tooling.

## Done (archive)

Major landed work (no action):

- Seed-data-context redesign (`data/seed.json`, graph: supervisor → build_context → invoke_specialists → assemble_response; no `core_data`).
- Phase 1 sync specialist research (LLM + Tavily, slices 1100–1400).
- Query-only public API (CLI/MCP `EntityQuery` / `query_entity`).
- Classification engine + Agent Factory + dynamic dispatch.
- Runtime data gitignored (`data/agents/`, registry, generated `*_specialist.py`, `categories.json`).
- `QueryResponse`: `results`, `message`, `debug`, `trace_id`, `thread_id`.
- Smoke/full test split; initial CRM seed (`data/seed_crm.json` → `data/seed.json`).
- Pre-redesign cleanup (derivative datasets, orchestrator→supervisor, ingestion handshake removed).

**Cancelled (obsolete after redesign):**

- ~~`routing.py` / `core_data_agent` follow-ups~~ — `core_data` removed; routing lives in supervisor + `dispatch.py` + graph nodes.

---

Last updated: 2026-06-14 (provisional validation bug queued; manual gate after fix; admin 1300–1305 done locally)
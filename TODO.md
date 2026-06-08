# Mycelium — TODO

Open tasks and roadmap (**Grok + Paul only** — Cursor reads for context, does not edit; see `prompts/cursor/WORKFLOW.md`).  
**Source of truth for architecture:** `docs/architecture.md`.  
**Implementation handoffs:** `prompts/cursor/next/` per `prompts/cursor/WORKFLOW.md`.

---

## Demo (phase)

Operator tooling for Paul’s demos (and future remote admin). **Slices 1 → 4 → 5 → 1200 + hands-on test: done** (June 2026). **MCP onboarding slices 1–4 done** (June 2026). **Next:** admin UI polish.

### Slice 1 — `refresh-example-network` — **done** (`2026-06-08-1000`)

- [x] **`bin/refresh-example-network <name>`** — shared logic in `src/network/example.py`; wipe + recopy; `--root`, `--register`, `--default`/`--no-default`, `--yes`, `--dry-run`.
- [x] **Removed `bin/copy-example-network`** — README, `examples/networks/crm/README`, integration tests updated.
- [x] **Retired legacy `data/` shim** — `resolve_network_root()` fails loud when unconfigured.
- [x] **Demo runbook** (README) — refresh before demos; restart MCP; fresh `thread_id` per attribute.

### Slice 2 — network status (CLI) — **done** (`2026-06-08-1100`)

- [x] **`mycelium network status`** — `src/network/introspection.py`; seed, ontology, specialists, storage stats; `--json`, `--category`, `--person`.
- [x] **Tests** — `tests/test_network_status.py` (empty + populated + JSON CLI + person drill-down).

### Slice 3 — admin daemon — **done** (`2026-06-08-1700`)

- [x] **`mycelium-admin` (`uv run mycelium-admin`)** — long-lived **HTTP** admin API on localhost (one process per network, like MCP). env: `MYCELIUM_NETWORK` / `MYCELIUM_NETWORK_ROOT`; default `127.0.0.1:8741`.
  - **v0 read-only:** `GET /health`, `GET /status` (mirrors `network status --json`), `GET /capabilities` via `src/network/introspection.py`.
  - **Later write ops:** refresh, register (slice 4+); remote + auth deferred.

### Slice 4 — admin UI — **done** (`2026-06-08-1800`)

- [x] **`mycelium-admin-ui`** (`admin-ui/`) — Vite + React SPA against admin daemon. Drill-down: network → specialists → entity → fields. Dev: `npm run dev`; demo: build + serve from `mycelium-admin`.
  - Local demos first; same API supports future remote deployments.

### Admin UI polish — **queued**

**Prompt:** `prompts/cursor/next/2026-06-08-2000-demo-admin-ui-polish.md`

- [ ] **Scannable overview** — ✅/❌ Seed, Ontology, Specialists; ontology in guide card; collapsed secondary panels; 3s silent `/status` poll.

### `bin/restart-admin` — **queued**

**Prompt:** `prompts/cursor/next/2026-06-08-2100-bin-restart-admin.md`

- [ ] **Dev stack restart** — kill :8741 + :5173; background `mycelium-admin` + foreground `npm run dev`; default network `crm`.

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

### Protocol & conversation

- [x] **Remove `list_specialist_routing` from MCP** — dropped public tool; `_routing_payload()` retained for `health_check` only (`2026-06-08-1400`).
- [x] **MCP onboarding for visiting agents** — **complete** (slices `1300`–`1600`: entity rename, specialist fixup, `guide.md` + `describe_network`, classification-aware messages, polish). Paul MCP live verify done (June 2026).
- [ ] **Fuzzy entity_key matching** — today `find_by_key` resolves by exact UUID or case-insensitive name equality only (`src/agents/seed.py`); typos and near-misses return not-found. Allow fuzzy matches on name (and later other seed fields): normalization (strip punctuation, collapse whitespace), optional phonetic/edit-distance threshold, rank candidates, return multiple close matches with disambiguation guidance in `message` (align with multi-match policy). Paul + Grok: spec match strategy, confidence floor, and whether fuzzy is opt-in (`entity_key` vs new field) before queuing.
- [ ] **Per-record query messages (multi-match)** — v1 keeps collective `message` when `entity_key` matches multiple seed records (e.g. two Kevin Zhangs); agent disambiguates via `results`. Revisit when non-person or other domains need per-record status in `message` (different attrs per match, async research diverging per id).
- [x] **Thread checkpoint: new query on same `thread_id`** — fixed (`run_query` clears stale `response`; removed `assemble_response` short-circuit; smoke test `test_same_thread_new_query_rebuilds_response`). **Follow-up:** multi-turn merge semantics (reuse specialist cache across attributes on one thread without redundant research) still open.
- [ ] **Long-running threads** — suspend and ask client for clarification (`thread_id` + checkpoints; bones exist).
- [ ] **Seed data vs specialists** — today the supervisor resolves `seed.json` (`find_by_key`), then `build_context` passes a seed slice into every specialist; generated specialists re-derive `id` from `context.seed` and research prompts include that seed. Awkward overlap: specialists effectively “check” seed for identity and research hints though seed is meant to be supervisor-owned origin data. Paul + Grok: lock boundaries — seed lookup/ambiguity only in supervisor; specialists receive resolved `current_id` + `target_fields` (and minimal research context, not full seed re-validation); clarify name/employer (seed vs specialist storage after 1710); align with **Seed from Queries** write path and **Data addition**. Update Jinja template + `context.py` peer-retrieval TODO when spec’d.

### Network launch v2 (design — Paul + Grok)

- [ ] **Seed from Queries** — queries can **create or enrich** seed records (not only read static `seed.json`). Includes **network launch v2** (no initial `--seed`; first queries establish origin records — disambiguate before research, e.g. generic “Paul Murphy” + address) and ongoing growth of the `people` array from validated query results. Paul + Grok: spec semantics, disambiguation, and write path before queuing. *v1 `network create` still requires `--seed`.*

## Future / deferred

- [ ] **Agent tools review** — today specialists get one LangChain tool (`web_search` via Tavily in `src/tools/research.py`); real networks will need dozens (structured lookups, enrichment APIs, calculators, file/DB access, handoffs, etc.). Paul + Grok: catalog required tools by domain, decide framework vs per-network tool packs, registry/discovery pattern, credential boundaries, and how factory-generated specialists bind tools — before scaling ontology/specialist count.
- [ ] **Per-network LangSmith projects (design discussion)** — framework-level `LANGCHAIN_PROJECT` today; optional `mycelium-<network>` per root; wire on `network create` later.
- [ ] **Non-person seed schemas** — v1 `--seed` validates person-shaped `people` array; generic entity seed for vehicles/organisms/artifacts deferred.
- [ ] **`network regen-ontology`** — re-run creation prompt against existing root (structural ontology refresh).
- [ ] **Per-network credentials (design discussion)** — Paul + Grok: keep today’s model (framework `.env` shared across networks) vs per-network API keys, `~/.config/mycelium/credentials`, MCP env templates on `network create`. **Current policy:** framework-level only; documented in README + architecture.
- [ ] **Distributed network discovery** — long-term; networks find each other without shared local config (prerequisite for inter-network handoff). v1 = local `~/.config/mycelium/networks.json` only.
- [ ] **Inter-network handoff** — query routing across networks (e.g. car → airplane); after distributed discovery.
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
- Query-only public API (CLI/MCP `EntityQuery` / `query_entity`).
- Classification engine + Agent Factory + dynamic dispatch.
- Runtime data gitignored (`data/agents/`, registry, generated `*_specialist.py`, `categories.json`).
- `QueryResponse`: `results`, `message`, `debug`, `trace_id`, `thread_id`.
- Smoke/full test split; initial CRM seed (`data/seed_crm.json` → `data/seed.json`).
- Pre-redesign cleanup (derivative datasets, orchestrator→supervisor, ingestion handshake removed).

**Cancelled (obsolete after redesign):**

- ~~`routing.py` / `core_data_agent` follow-ups~~ — `core_data` removed; routing lives in supervisor + `dispatch.py` + graph nodes.

---

Last updated: 2026-06-08 (demo slice 4 admin UI done)
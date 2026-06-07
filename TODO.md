# Mycelium — TODO

Open tasks and roadmap. **Source of truth for architecture:** `docs/architecture.md`.  
**Implementation handoffs:** `prompts/cursor/next/` per `prompts/cursor/WORKFLOW.md`.

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

**Plan:** `docs/plans/networks-terminology.md` (staged phases). **Order:** Phases 1–4 → **integration testing** → optional **polish squirts** → Phase 5. **Cursor queue:** Phase 4 (`1300`), then integration testing (`1400`).

### Terminology & bootstrap

- [x] **Networks terminology (Phase 1)** — docs: framework vs network root, default network, MCP-per-network (slice `2026-06-09-1000`).
- [x] **Network path resolver (Phase 2)** — `MYCELIUM_NETWORK_ROOT`, CLI `--network-dir`, legacy `data/` shim (slice `2026-06-09-1100`).
- [x] **Network registry + default (Phase 3)** — `network list|register|use`, config file (slice `2026-06-09-1200`).
- [ ] **CRM example network (Phase 4)** — `examples/networks/crm/` in repo (evolving reference); remove flat `data/` seed from default clone.
- [ ] **Networks integration testing (Phase 4.5)** — serious CLI/MCP/multi-root/registry tests **before Phase 5** (slice `2026-06-07-1400` queued).
- [ ] **Network creation prompt (Phase 5)** — ontology of specialist agents (not fixed six-category default); **after testing + polish window**.
- [ ] **Custom specialists** per network (Phase 5).

### Networks polish (short-term — squirt after Phase 4)

Small tasks; pick any as a one-off Cursor slice between Phase 4 and Phase 5:

- [ ] `health_check` — expose `network_display_name` from `network.json` in `info`.
- [ ] `health_check` error path — `network_root` fallback via `framework_root() / "data"`, not cwd `data/`.
- [ ] `.env.example` — document `MYCELIUM_NETWORK_ROOT`, `MYCELIUM_FRAMEWORK_ROOT`, `MYCELIUM_NETWORKS_CONFIG`.
- [ ] Legacy `mycelium seed` — wire `_configure_network_paths` or deprecate clearly in help text.
- [ ] `docs/full-code-walkthrough.md` — remove stale `core_data_agent` references.
- [ ] README — disambiguate “Phase 1 research” vs “Networks Phase N” in Status section.
- [ ] MCP instructions — include resolved network name when registry/`network.json` provides it.

### Protocol & conversation

- [ ] **Long-running threads** — suspend and ask client for clarification (`thread_id` + checkpoints; bones exist).
- [ ] **Query-as-seed** — unknown people created from queries; disambiguate before research (e.g. generic “Paul Murphy” + address).

## Future / deferred

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
- Query-only public API (CLI/MCP `PersonQuery`).
- Classification engine + Agent Factory + dynamic dispatch.
- Runtime data gitignored (`data/agents/`, registry, generated `*_specialist.py`, `categories.json`).
- `PersonResponse`: `results`, `message`, `debug`, `trace_id`, `thread_id`.
- Smoke/full test split; initial CRM seed (`data/seed_crm.json` → `data/seed.json`).
- Pre-redesign cleanup (derivative datasets, orchestrator→supervisor, ingestion handshake removed).

**Cancelled (obsolete after redesign):**

- ~~`routing.py` / `core_data_agent` follow-ups~~ — `core_data` removed; routing lives in supervisor + `dispatch.py` + graph nodes.

---

Last updated: 2026-06-07 (testing before Phase 5; networks polish backlog added)
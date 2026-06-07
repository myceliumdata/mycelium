# Networks — Terminology, Namespaces & Packaging Plan

**Status:** Draft for review (June 2026)  
**Audience:** Paul + Grok (planning); Cursor (implementation slices after approval)  
**Depends on:** `TODO.md` → Product vision — Networks → Terminology & bootstrap

---

## Why this doc exists

**Product model (Paul, June 2026):** Users download the **Mycelium framework** (this repo) and **launch named networks**. Each network lives in its **own namespace** (isolated seed, ontology, registry, specialist storage, checkpoints). The repo today still embeds **CRM prototype data** (`data/seed.json`, `seed_crm.json`, `raw_data.json`, etc.) from early development—that must move out so the framework is domain-neutral.

The TODO item “rename instance → network” is therefore **not** a mechanical find-and-replace (the word *instance* barely appears). It is:

1. **Terminology** — *network* is the product noun for a named namespace users launch.
2. **Packaging** — separate framework code from network-specific data.
3. **Layout** — per-network paths and env resolution (replacing flat `data/` assumptions).
4. **UX** — eventually `network create` / `network launch` (or equivalent) with a creation prompt defining specialist ontology.

README/architecture already say “networks of LangGraph agents” (the agent collective). This plan adds the **named network namespace** sense and disambiguates overloads.

---

## Core definition

### Network (product noun)

A **network** is a **scoped Mycelium deployment** that owns:

| Artifact | Today (prototype — CRM in repo) | Target (per named network) |
|----------|----------------------------------|----------------------------|
| Seed origin | `data/seed.json` *(committed CRM seed)* | `networks/<name>/seed.json` *(user data, gitignored)* |
| Classification ontology | `data/categories.json` | `networks/<name>/categories.json` |
| Specialist registry | `data/agent_registry.json` | `networks/<name>/agent_registry.json` |
| Specialist storage | `data/agents/<category>/` | `networks/<name>/agents/<category>/` |
| Generated specialists | `src/agents/specialists/*_specialist.py` | per-network generated modules or dynamic load path |
| Checkpoints | `data/checkpoints.sqlite` | `networks/<name>/checkpoints.sqlite` |
| SQLite legacy DB | `data/mycelium.db` | `networks/<name>/mycelium.db` (if retained) |
| LangSmith project | `LANGCHAIN_PROJECT=mycelium` | `mycelium-<name>` or caller-configured |

**Framework vs network data:**

| Layer | Lives in repo | Examples |
|-------|---------------|----------|
| **Framework** | Yes (committed) | `src/`, `bin/`, docs, tests, empty `networks/` scaffold |
| **Example network** | Optional `examples/` or `networks/_template/` | Tiny demo seed, not Paul's CRM |
| **User networks** | No (gitignored) | `networks/prm_crm/`, `networks/car_fleet/` |

A network is **not** the same as:

- A **LangGraph graph** (one compiled graph serves queries inside a network today).
- A **specialist agent** (one node/domain owner inside a network).
- A **conversation thread** (`thread_id` — session within a network).
- A **social network profile** (LinkedIn, X — attribute domain; see below).

**Examples (vision):**

- **CRM network** — people at funds/startups; contact, professional, social specialists (today’s default).
- **Car network** — vehicles, specs, ownership; different ontology and specialists.
- **Airplane network** — fleet/regulatory domain; handoff from car network when a person owns both.

---

## Terminology map (use consistently)

| Term | Meaning | Use when | Avoid |
|------|---------|----------|-------|
| **Network** | Scoped deployment + ontology + data | Product, docs, MCP instructions, env naming | “Instance,” “deployment,” “tenant” (unless infra context) |
| **Active network** | The named namespace currently selected for CLI/MCP | “Launch network `prm_crm`” | “Default” without explaining selection |
| **Framework** | Downloadable Mycelium project (code + tooling) | README quick start | Confusing with a network |
| **Agent network** / **specialist graph** | LangGraph topology inside one network | Architecture (supervisor → specialists) | Bare “network” when domain profiles are meant |
| **Supervisor** | Coordinator/router inside a network | Code and docs (unchanged) | “Orchestrator,” “god agent” |
| **Specialist** | Domain-owning agent inside a network | Code and user-facing | “Sub-agent” without context |
| **Seed** | Static origin people list for a network | `data/seed.json`, loader docs | “Core table,” “CRM dump” |
| **Social profile** / **professional profile** | LinkedIn, X, etc. (attributes) | Classification descriptions, `social` category | “Social network” alone (ambiguous) |
| **Thread** | `thread_id` conversation/checkpoint scope | CLI/MCP session continuity | “Network” for sessions |
| **Handoff** | Cross-network discovery/routing (future) | Roadmap, protocol design | “Query federation” without definition |

---

## Disambiguating “network” in existing text

Three distinct senses appear today:

1. **Product network** — “CRM network,” “car network” *(introduce explicitly)*  
2. **Agent collective** — “networks of LangGraph agents” in architecture overview *(keep; clarify = agent collective inside one product network)*  
3. **Social/professional networks** — category description for LinkedIn/X *(rename to “profiles” or “social/professional profiles” in user-facing strings where confusion matters)*

**Recommended doc tweak (architecture overview):**

> Mycelium organizes people data into **networks**—each network is a scoped ecosystem of specialist agents. Within a network, a **supervisor** coordinates a graph of specialists that classify, research, and persist attributes.

---

## Today vs target (honest framing)

### Today (June 2026 — prototype debt)

- Flat `data/` layout; paths hardcoded or via `MYCELIUM_*_PATH` env vars.
- **CRM seed committed in repo** (`data/seed.json`, `seed_crm.json`, `raw_data.json`, `prepare_seed.py`).
- Behaves like one network per checkout, but there is no **network name** or launcher.
- Categories seeded from code (`_SEED_CATEGORIES`); six-ish default domains.
- Inter-network handoff: not implemented.

### Target (Paul’s model)

1. Clone/download **framework** — no private CRM data in tree.
2. **Create** a named network (creation prompt → ontology of specialists, not fixed six categories).
3. **Launch** / select active network — all queries, MCP, checkpoints scoped to `networks/<name>/`.
4. Multiple networks on one machine; optional inter-network handoff later.

**Principle:** Docs and UX say **network** = named namespace. Until migration ships, call current behavior **legacy flat layout** or **pre-networks prototype**—not “multi-network ready.”

---

## Naming conventions (future-proofing)

Use these in docs now; code adopts when multi-network lands.

| Concept | Recommended id form | Display name | Notes |
|---------|---------------------|--------------|-------|
| Network name | `snake_case` slug | Title Case | e.g. `prm_crm`, `car_fleet` — user-chosen at create |
| Active network | `MYCELIUM_NETWORK` env or CLI `--network` | — | Required once multi-network ships |
| Namespace root | `networks/<name>/` | — | All runtime artifacts under here |
| MCP | `cwd` = framework root; `MYCELIUM_NETWORK` selects namespace | — | Or per-network MCP config later |

Do **not** rename Python `isinstance`, factory singletons, or Cursor “instance” in `PARALLEL_EXECUTION_GUIDE.md`.

---

## Phased work (revised scope)

Renaming/clarification spans multiple slices. **Do not lump namespace migration into a doc-only pass.**

### Phase 1 — Terminology docs (small, safe)

Doc + user-facing strings only; acknowledge prototype CRM-in-repo as debt.

- `docs/architecture.md` — Networks section (framework vs network namespace).
- `README.md` — “Download framework → create/launch named networks”; note current flat `data/` is transitional.
- Disambiguate “social profiles” vs product “network” in category copy (optional).
- MCP instructions: active network / namespace (wording only until Phase 2).

### Phase 2 — Namespace layout + path resolver (medium)

Introduce `networks/<name>/` and central path resolution (replaces scattered `MYCELIUM_*_PATH` defaults).

- `MYCELIUM_NETWORK` (or `MYCELIUM_NETWORKS_ROOT` + active name).
- Single helper, e.g. `network_paths.py`, used by seed, registry, factory, storage, checkpoints, MCP bootstrap.
- **Migration shim:** if `MYCELIUM_NETWORK` unset, fall back to legacy `data/` (backward compat for dev).
- Tests use temp `networks/test_net/`.

### Phase 3 — Extract CRM from repo (medium, user-visible)

Move prototype CRM data out of committed tree.

| Current (committed) | Proposed |
|-------------------|----------|
| `data/seed.json` | `examples/networks/prm_crm/seed.json` or local-only after import |
| `data/seed_crm.json`, `raw_data.json` | `examples/` or remove from default clone |
| `data/prepare_seed.py` | `bin/` or `examples/scripts/` |

- Gitignore `networks/*/` (keep `networks/.gitkeep` or `networks/_template/`).
- README quick start: create network from template or minimal demo seed (3–5 people).
- Paul's CRM: lives in `networks/prm_crm/` locally, not pushed.

### Phase 4 — Network launcher + creation prompt (larger)

- CLI: `mycelium network create <name>`, `mycelium network use <name>`, `mycelium network list`.
- Creation prompt produces ontology (specialists/categories), not fixed six-category default.
- Custom specialists per network (ties to agent factory).

### Phase 5 — Inter-network handoff (future)

Discovery and query routing across named namespaces.

---

## What “rename instance → network” means now

| In scope | Out of scope |
|----------|--------------|
| Product noun **network** = named namespace | Renaming Python `isinstance` |
| Framework vs network data separation (plan + phases) | Inter-network protocol (Phase 5) |
| Moving CRM seed out of default repo | Full ontology LLM on day one |
| `networks/<name>/` layout | Renaming every `data/` symbol in one PR |

---

## Open questions for Paul

1. **Namespace root** — `networks/<name>/` at repo root (preferred?) vs `~/.mycelium/networks/<name>/` for user data outside clone?
2. **CRM migration** — Move to `examples/networks/prm_crm/` in repo for docs, or entirely local/gitignored with import script?
3. **Active network selection** — Env-only (`MYCELIUM_NETWORK`), CLI flag (`--network`), or both?
4. **Non-person networks** — Same noun “network” for cars/airplanes, or always qualified (“vehicle network”)?
5. **Phase order** — Phase 1 docs now, then Phase 2+3 together (paths + CRM extract), or paths before docs?

---

## Related roadmap (separate plans)

| Item | Prerequisite |
|------|----------------|
| Network creation prompt | This terminology + ontology design doc |
| Custom specialists per network | Network creation + storage layout |
| Inter-network handoff | Network id + discovery protocol |
| Query-as-seed | Largely orthogonal; same default network |

---

## Success criteria

- **Terminology:** “Network” = user-launched named namespace; “framework” = downloadable Mycelium project.
- **Packaging:** Default clone is CRM-free; prototype data is example or user-local.
- **Runtime:** Queries resolve paths under active `networks/<name>/` (after Phase 2+).
- **Honesty:** Docs describe prototype flat `data/` as transitional until migration lands.

**Last updated:** 2026-06-06 (revised per Paul — named namespaces + CRM extract)
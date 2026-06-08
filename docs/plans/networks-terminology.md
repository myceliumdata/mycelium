# Networks — Terminology, Namespaces & Packaging Plan

**Status:** Approved (June 2026) — Paul decisions incorporated below. **Delivered:** Networks Phases 1–5 (`2026-06-09-1000` … `1800`): path resolver, registry, CRM example, integration testing (`1400`), **`network create`** with per-network `specialists/` and skeleton ontology (`1500`–`1800`). **Next:** query-as-seed (v2), inter-network handoff (Phase 6).
**Audience:** Paul + Grok (planning); Cursor (implementation slices after approval)  
**Depends on:** `TODO.md` → Product vision — Networks → Terminology & bootstrap

---

## Why this doc exists

**Product model (Paul, June 2026):** Users download the **Mycelium framework** (this repo) and **launch named networks**. Each network lives in its **own namespace** (isolated seed, ontology, registry, specialist storage, checkpoints). **Phase 4 complete:** CRM seed no longer ships in repo-root `data/` — bootstrap from committed **`examples/networks/crm/`** via `bin/refresh-example-network crm` into a user-chosen `network_root`.

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

| Artifact | Today (prototype — CRM in repo) | Target (under **network root**) |
|----------|----------------------------------|--------------------------------|
| Network manifest | — | `<network_root>/network.json` (name, metadata) |
| Seed origin | `data/seed.json` *(committed CRM seed)* | `<network_root>/seed.json` |
| Classification ontology | `data/categories.json` | `<network_root>/categories.json` |
| Specialist registry | `data/agent_registry.json` | `<network_root>/agent_registry.json` |
| Specialist storage | `data/agents/<category>/` | `<network_root>/agents/<category>/` |
| Generated specialists | `src/agents/specialists/*_specialist.py` (CRM reference) | `<network_root>/specialists/*_specialist.py` (Phase 5) |
| Checkpoints | `data/checkpoints.sqlite` | `<network_root>/checkpoints.sqlite` |
| SQLite legacy DB | `data/mycelium.db` | `<network_root>/mycelium.db` (if retained) |
| LangSmith project | `LANGCHAIN_PROJECT=mycelium` | `mycelium-<name>` or caller-configured |

### Network root (primary selector)

A network is identified by **`network_root`**: an absolute path to a directory the user chooses at create time. All runtime artifacts live under that directory using a **standard layout** (contract below). The path may be anywhere on disk — inside the repo, outside the clone, on Dropbox, etc.

**Framework vs network data:**

| Layer | Lives where | Examples |
|-------|-------------|----------|
| **Framework** | Repo clone (committed) | `src/`, `bin/`, docs, tests |
| **Example network** | `examples/networks/` (committed, tiny) | Demo seed for quick start |
| **User networks** | User-chosen paths (never committed) | `~/mycelium-networks/prm_crm/`, `/data/mycelium/car_fleet/` |

**Standard layout under `network_root`:**

```
<network_root>/
  network.json          # name, display_name, created_at, …
  seed.json
  categories.json       # runtime; seeded on first use
  agent_registry.json
  specialists/          # generated *_specialist.py (Phase 5)
  agents/<category>/storage.json
  checkpoints.sqlite
  mycelium.db           # optional legacy
```

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
| **Network root** | User-chosen directory holding all network data | CLI `--network-dir`, env `MYCELIUM_NETWORK_ROOT` | Fixed path under repo only |
| **Default network** | Registered network used when no dir/name passed | `mycelium query` with no flags | Ambiguous “active” without config |
| **Named network** | Logical name in `network.json` + optional registry | `mycelium query --network prm_crm` | Name without resolvable path |
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

### Target (Paul’s model — June 2026 decisions)

1. Clone/download **framework** — no private CRM data in default tree.
2. **Create** a network: user picks **name** and **`network_root` path** (where data lives).
3. **Query** via CLI with **`--network-dir`** (path) or **`--network`** (name → resolved via registry); if omitted, use **default network**.
4. **MCP:** one **long-lived server process per network**; run several in parallel with different `MYCELIUM_NETWORK_ROOT` in each client config. Framework `cwd` stays the repo; data paths come from env.
5. Optional inter-network handoff later (Phase 6).

**Principle:** **Network root path** is the runtime source of truth. Name is metadata + convenience alias. Until migration ships, legacy flat `data/` remains the implicit default network root for dev.

---

## Selection model (CLI, env, MCP)

### Resolution order (proposed)

When a query runs, resolve `network_root` in this order:

1. CLI **`--network-dir /absolute/path`** (explicit path; highest precedence)
2. CLI **`--network prm_crm`** (lookup in network registry → path)
3. Env **`MYCELIUM_NETWORK_ROOT`** (explicit path; used by MCP and scripts)
4. Env **`MYCELIUM_NETWORK=prm_crm`** (name lookup)
5. **Default network** from user config (see below)
6. **Legacy shim:** repo `data/` if nothing else configured (prototype compat)

### Default network

Paul: a **default network** makes sense. Proposed:

- User config file (e.g. `~/.config/mycelium/networks.json` or `.mycelium/networks.json` in home) maps **name → network_root** and marks one entry as `default: true`.
- Env override: `MYCELIUM_DEFAULT_NETWORK` (name) or `MYCELIUM_DEFAULT_NETWORK_ROOT` (path).
- `mycelium query` with no network flags uses the default.
- First-time setup: `mycelium network init` or `network register` seeds config from an existing path.

### What the config file is for (Phase 3)

The **networks config** is a small user-local registry so you do not have to type full paths every time. It is **not** where network data lives — only **pointers**.

**Problem it solves:** You chose `network_root` at create time (maybe `~/Dropbox/mycelium/prm_crm`). Without config, every CLI call needs `--network-dir ~/Dropbox/mycelium/prm_crm`. With config, you register once and use `--network prm_crm` or rely on the default.

**Example `~/.config/mycelium/networks.json`:**

```json
{
  "version": "1",
  "networks": [
    {
      "name": "prm_crm",
      "root": "/Users/paul/mycelium-networks/prm_crm",
      "default": true
    },
    {
      "name": "car_fleet",
      "root": "/Users/paul/mycelium-networks/car_fleet",
      "default": false
    }
  ]
}
```

| Config stores | Config does **not** store |
|---------------|---------------------------|
| Network **name** (short alias) | `seed.json`, agents, registry |
| **Absolute path** to `network_root` | Specialist generated code |
| Which entry is **default** | Checkpoints or research cache |

**MCP note:** Parallel MCP servers usually set `MYCELIUM_NETWORK_ROOT` directly in the client JSON (explicit per server). Config is optional for MCP; it shines for CLI convenience and `mycelium query` with no flags.

**Phase 2 does not require config** — `--network-dir` and `MYCELIUM_NETWORK_ROOT` are enough. Config arrives in Phase 3 with `network register` / `network use`.

### CLI (target)

```bash
# Explicit path
uv run mycelium query --network-dir ~/mycelium-networks/prm_crm --person-key "…"

# By registered name
uv run mycelium query --network prm_crm --person-key "…"

# Default network (from config)
uv run mycelium query --person-key "…"

# Network management (later phases)
uv run mycelium network create prm_crm --root ~/mycelium-networks/prm_crm
uv run mycelium network list
uv run mycelium network use prm_crm   # set default
```

### MCP — one server per network (parallel)

Each MCP process binds to **one** `network_root` for its lifetime. Multiple networks = multiple MCP entries in the client (Claude Desktop, etc.):

```json
{
  "mycelium-prm-crm": {
    "command": "uv",
    "args": ["run", "mycelium-mcp"],
    "cwd": "/absolute/path/to/mycelium",
    "env": {
      "MYCELIUM_NETWORK_ROOT": "/Users/paul/mycelium-networks/prm_crm"
    }
  },
  "mycelium-car-fleet": {
    "command": "uv",
    "args": ["run", "mycelium-mcp"],
    "cwd": "/absolute/path/to/mycelium",
    "env": {
      "MYCELIUM_NETWORK_ROOT": "/Users/paul/mycelium-networks/car_fleet"
    }
  }
}
```

- No network switching inside a single MCP process (keeps long-lived reload semantics simple).
- `refresh_runtime_from_disk()` reloads **that** network’s files only.
- MCP tool instructions should state which network name/path the server is bound to (from `network.json`).

### Env vars (consolidation target)

**Credentials:** `OPENAI_API_KEY`, `TAVILY_API_KEY`, `LANGCHAIN_*`, etc. stay in the **framework** `.env` (process-wide). They are **not** per-network and are **not** written into `network_root`. MCP parallel servers reuse the same keys; only `MYCELIUM_NETWORK_*` differs per entry.

| Variable | Purpose |
|----------|---------|
| `MYCELIUM_NETWORK_ROOT` | Absolute path to network data directory (primary for MCP) |
| `MYCELIUM_NETWORK` | Registered network name (alternative selector) |
| `MYCELIUM_DEFAULT_NETWORK` | Default network name |
| `MYCELIUM_DEFAULT_NETWORK_ROOT` | Default network path (bypass registry) |
| `MYCELIUM_NETWORKS_CONFIG` | Path to name→root registry JSON (optional) |

Per-artifact `MYCELIUM_SEED_PATH`, `MYCELIUM_AGENT_REGISTRY_PATH`, etc. become **derived** from `network_root` (still overridable in tests).

Do **not** rename Python `isinstance`, factory singletons, or Cursor “instance” in `PARALLEL_EXECUTION_GUIDE.md`.

---

## Phased work (staged — Paul approved approach)

Large effort; ship in **independent slices** with legacy `data/` shim until each phase lands.

### Phase 1 — Terminology + architecture docs (small)

- Document framework vs network, **network root**, default network, MCP-per-network model.
- `docs/architecture.md`, `README.md`, link to this plan.
- No runtime changes.

**Cursor slice:** doc-only, ~1 session.

### Phase 2 — Network path resolver + CLI/MCP wiring (medium — core)

**Goal:** Any command can target any `network_root`; default network when omitted.

- New module e.g. `src/network/paths.py` (or `src/storage/network_root.py`):
  - `resolve_network_root(cli_dir=, cli_name=, env) -> Path`
  - Derive seed, registry, agents, checkpoints, DB paths from root.
- Wire into `main.py`, `mycelium_mcp/server.py` `_bootstrap()` (path resolver; no reset script).
- CLI: `--network-dir`, `--network` on `query` (and global default resolution).
- MCP: read `MYCELIUM_NETWORK_ROOT`; include network name in `health_check` / instructions.
- **Legacy shim:** unset → `data/` under framework root (current behavior).
- Smoke tests with `tmp_path` network roots.

**Cursor slice:** bounded; no network registry file yet (path + env only).

### Phase 3 — Default network registry + `network` CLI stubs (medium)

- Config: `~/.config/mycelium/networks.json` (or similar) — `{ "networks": [{ "name", "root", "default" }] }`.
- `mycelium network register`, `network list`, `network use` (set default).
- `--network <name>` resolves through registry.

### Phase 4 — CRM example network in repo + extract from `data/` (medium, visible)

Paul: **keep a CRM example in the repo** — it will evolve with the product.

- Add **`examples/networks/crm/`** — full standard `network_root` layout (seed, manifest, optional starter categories). Committed, public-safe subset or synthetic rows; grows over time as the reference network.
- Remove runtime CRM from flat **`data/`** in default clone (no private seed at repo root).
- README quick start: copy or link example → user-chosen path, then `network register` / set default.
- Optional `bin/refresh-example-network crm` to bootstrap a local network from `examples/networks/crm/`.
- Paul's live CRM stays at a user path (not necessarily committed).

### Phase 4.5 — Integration testing — **delivered** (`2026-06-09-1400`)

- Multi-network CLI isolation (`--network-dir`, `--network`, default).
- Parallel MCP: two roots, `health_check` + `query_person` parity.
- Example-network copy → register → query happy path.
- Checkpoint/thread hygiene (unique `thread_id` per scenario; document stale-thread gotcha).
- `tests/test_network_integration.py`; MCP path preservation fix in `refresh_runtime_from_disk`.

### Networks polish (short-term squirt)

After Phase 4, one bounded slice from `TODO.md` → **Networks polish** (`2026-06-09-1350`) **before** Phase 4.5 integration testing. Not blocking Phase 5.

### Phase 5 — Network launch v1 — **delivered** (`1500`–`1800`)

See [`docs/plans/networks-phase5.md`](networks-phase5.md) for full design.

- **`mycelium network create`** — `--root`, required `--seed`, creation `--prompt` (or `--prompt-file`); optional `--display-name`, `--default`, `--dry-run`, `--force`, `--no-mcp-snippet`.
- **Skeleton ontology** at create: LLM maps creation prompt → `categories.json` + `agent_registry.json` + minimal `attribute_map` (examples only).
- **Per-network specialists:** `<network_root>/specialists/` via `MYCELIUM_SPECIALISTS_DIR`; isolated from other networks on the same machine.
- **Classification unchanged:** unknown attributes still classify lazily at query time; supervisor can create specialists on demand.
- **CRM path unchanged:** `bin/refresh-example-network crm` for committed reference; `network create` for custom domains.
- **Cleanup:** `bin/reset-mycelium` removed (`1760`) — start a new `--root` or `network create --force` instead.

### Phase 6 — Inter-network discovery & handoff (future)

**v1 (Phase 3):** Local config file maps names → `network_root` paths on one machine.

**Later (Paul):** Distributed discovery so networks can **find each other** without a shared local config — prerequisite for real inter-network handoff. Separate protocol plan; out of scope until path resolver + registry are stable.

---

### Suggested implementation order

```
Phase 1 → 2 → 3 → 4 (CRM example)
       → polish squirt (1350)
       → categories sample + alignment (1380)
       → 4.5 (integration testing) ✓
       → 5 (create prompt + ontology) ✓
       → 6 (distributed discovery + handoff)
```

Phase 2 unlocks parallel MCP servers immediately (different `MYCELIUM_NETWORK_ROOT` per config entry).

---

## What “rename instance → network” means now

| In scope | Out of scope |
|----------|--------------|
| Product noun **network** = named namespace | Renaming Python `isinstance` |
| Framework vs network data separation (plan + phases) | Inter-network protocol (Phase 6) |
| Moving CRM seed out of default repo | Full ontology LLM on day one |
| `networks/<name>/` layout | Renaming every `data/` symbol in one PR |

---

## Decisions (Paul — locked)

| Topic | Decision |
|-------|----------|
| Where data lives | User chooses **`network_root` path** at create time |
| CLI selection | **`--network-dir`** (path); **`--network`** (name via registry) in addition |
| MCP | **One server per network**; multiple servers in parallel; env `MYCELIUM_NETWORK_ROOT` |
| Default | **Yes** — default network when flags/env omit selection |
| Name→path registry | **Local config file** first (`~/.config/mycelium/networks.json` or equivalent) — good v1 |
| Network discovery | **Future:** distributed way for networks to find each other (Phase 6+ / separate protocol); not in v1 |
| CRM example | **`examples/networks/crm/`** in repo — evolving reference network |
| Delivery | **Staged phases** (this doc) |

## Open questions (remaining)

1. ~~**Config file location**~~ — **Decided:** `~/.config/mycelium/networks.json` default; override via `MYCELIUM_NETWORKS_CONFIG`.
2. ~~**CRM in repo**~~ — **Decided:** `examples/networks/crm/` committed reference network (evolves over time).
3. **Non-person networks** — Same noun “network” for cars/airplanes? (Yes — ontology is domain-agnostic; v1 seed loader still expects person-shaped `people` array; deferred generic seed schemas in `TODO.md`.)
4. ~~**Generated specialists**~~ — **Decided:** `<network_root>/specialists/` (Phase 5a); CRM reference modules remain under `src/agents/specialists/`.
5. ~~**Phase 5 queue**~~ — **Done** (slices `1500`–`1800` in `prompts/cursor/done/`).

---

## Related roadmap (separate plans)

| Item | Prerequisite |
|------|----------------|
| Network creation prompt | This terminology + ontology design doc |
| Custom specialists per network | Network creation + storage layout |
| Inter-network handoff | Distributed discovery + handoff protocol (post local config) |
| Query-as-seed | Largely orthogonal; same default network |

---

## Success criteria

- **Terminology:** “Network” = user-launched named namespace; “framework” = downloadable Mycelium project.
- **Packaging:** Default clone is CRM-free; prototype data is example or user-local.
- **Runtime:** Queries resolve paths under user-chosen **`network_root`** (after Phase 2+).
- **MCP:** Parallel servers each bound to one root via env.
- **Honesty:** Docs describe prototype flat `data/` as transitional until migration lands.

**Last updated:** 2026-06-09 (Phase 5 delivered; specialists layout; open questions closed)
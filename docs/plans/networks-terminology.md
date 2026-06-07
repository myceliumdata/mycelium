# Networks — Terminology & Naming Plan

**Status:** Draft for review (June 2026)  
**Audience:** Paul + Grok (planning); Cursor (implementation slices after approval)  
**Depends on:** `TODO.md` → Product vision — Networks → Terminology & bootstrap

---

## Why this doc exists

The roadmap uses **network** as the primary product noun (a bounded people-data ecosystem with its own specialist ontology). README and architecture already say “networks of LangGraph agents,” but the codebase today runs as a **single implicit network** with no `network_id`, no network creation flow, and no inter-network protocol.

The TODO item “rename instance → network” is **forward-looking**: the word *instance* does not appear in user-facing docs or code today (only Python `isinstance`, factory “instance,” Cursor “instance”). This plan **introduces** network terminology and disambiguates overloads—not a mechanical find-and-replace.

---

## Core definition

### Network (product noun)

A **network** is a **scoped Mycelium deployment** that owns:

| Artifact | Today (single network) | Future (per network) |
|----------|------------------------|----------------------|
| Seed origin | `data/seed.json` | `data/networks/<network_id>/seed.json` (illustrative) |
| Classification ontology | `data/categories.json` | per-network categories |
| Specialist registry | `data/agent_registry.json` | per-network registry |
| Specialist storage | `data/agents/<category>/` | per-network storage roots |
| Generated specialists | `src/agents/specialists/*_specialist.py` | per-network or namespaced modules |
| Checkpoints | `data/checkpoints.sqlite` | per-network or namespaced threads |
| LangSmith project | `LANGCHAIN_PROJECT=mycelium` | per-network tracing project (optional) |

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
| **Default network** | Implicit single-network mode (current) | Describing today’s behavior before multi-network ships | Pretending multi-network already exists |
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

### Today (June 2026)

- One implicit **default network** per repo checkout / MCP `cwd`.
- No `network_id` in `PersonQuery`, `PersonResponse`, or MCP tools.
- Categories seeded from code (`_SEED_CATEGORIES`); six-ish default domains.
- Inter-network handoff: not implemented.

### Target (roadmap — not this slice)

- Explicit network creation (prompt → ontology of specialists).
- Custom specialists per network.
- `network_id` or network selector on queries (design TBD).
- Inter-network discovery and handoff protocol.

**Principle:** Terminology docs and user-facing copy should describe **network** as the product noun while clearly labeling current builds as **single-network / default network** mode.

---

## Naming conventions (future-proofing)

Use these in docs now; code adopts when multi-network lands.

| Concept | Recommended id form | Display name | Notes |
|---------|---------------------|--------------|-------|
| Network id | `snake_case` or `kebab-case` slug | Title Case | e.g. `crm`, `car_fleet` |
| Env prefix (future) | `MYCELIUM_NETWORK_ID` | — | Default `default` or unset = current behavior |
| Data root (future) | `data/networks/<network_id>/` | — | Migration path from flat `data/` |
| MCP (future) | `network_id` optional on `query_person` | — | Default network when omitted |

Do **not** rename Python `isinstance`, factory singletons, or Cursor “instance” in `PARALLEL_EXECUTION_GUIDE.md`.

---

## What changes in slice 1 (terminology only)

**In scope — docs + user-facing strings, no runtime behavior change:**

1. **`docs/architecture.md`** — Add “Networks” section: definition, default network, disambiguation, link to this plan.
2. **`README.md`** — Lead with network concept; state “this repo runs one default network”; roadmap pointer.
3. **`TODO.md`** — Mark terminology slice criteria (not done until review).
4. **Classification category descriptions** — Optional: “social and professional **profiles**” instead of “network profiles” in `engine.py` seed categories and generated specialist headers (small, user-visible).
5. **`docs/full-code-walkthrough.md`** — Align overview paragraph if it mentions agents/networks vaguely.
6. **MCP `instructions` string** — One sentence: queries run against the default network for this server’s `cwd`.

**Out of scope for slice 1:**

- `network_id` field on models
- Multi-network data paths
- Network creation prompt / ontology bootstrap
- Inter-network handoff
- Renaming code symbols (`graphs`, `registry` paths unchanged)

---

## Cursor slice proposal (after Paul approves this plan)

**Slug:** `2026-06-09-1100-networks-terminology-docs` (or next available timestamp)

**Objective:** Doc-only terminology alignment per “What changes in slice 1” above.

**Verification:** No test changes required; `grep` audit that user-facing “instance” (product sense) is absent and “default network” appears in README + architecture.

---

## Open questions for Paul

1. **Default network name** — Use `default`, `crm`, or name after primary seed (e.g. `prm_crm`)? Affects future paths and LangSmith project naming.
2. **“Social network” in category copy** — Change to “social profiles” everywhere, or keep in technical classification metadata?
3. **Public branding** — Is a network always “people data,” or can non-person networks (cars, airplanes) share the same noun without qualifier (“vehicle network”)?
4. **Slice 1 timing** — Docs-only now, or wait until network creation design is sketched?

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

- Readers can answer: “What is a Mycelium network?” in one sentence.
- No ambiguous “network” without context in README or architecture.
- Current single-network behavior is explicit—not implied multi-network.
- Cursor has a bounded doc-only slice ready in `prompts/cursor/next/` after approval.

**Last updated:** 2026-06-06 (draft)
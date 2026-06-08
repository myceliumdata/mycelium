# Design conversation: Entity registry, validation & network growth

**Date:** 2026-06-08  
**Participants:** Paul, Grok  
**Status:** Design captured — path not clear yet; reason over before code  
**Distilled in:** `TODO.md` → **Entity registry, validation & growth** (+ links from Seed from Queries, Seed vs specialists, Data addition)  
**Related:** companion doc [entity-key-negotiation.md](2026-06-08-entity-key-negotiation.md), `docs/architecture.md` (seed-data-context), `docs/plans/seed-data-context-architecture.md`

---

## Paul — opening problem

This follows the entity-key / negotiation thread but adds **adding new data** and something **under the surface**: **when does seed data get validated?**

### Constraints Paul stated

1. **The store must grow** — we can’t have a data store that never grows.
2. **Unknown entities** — a request for **Paul Murphy** (not seeded) should become a request for **more information**, not immediate failure or silent invention.
3. **Desired response shape** — Mycelium should say something like: *“I don’t have any information about Paul Murphy, but if you tell me who he currently works for, I might be able to help.”*
4. That implies a **minimum viable record** per network — for CRM: **name + employer** as core binding fields before the network can help further.
5. **Ambiguous seed ↔ specialist relationship today** — Paul wants this fixed:
   - For CRM, **demographic** specialist should validate **name**
   - **Professional** specialist should validate **company**
   - They must **cooperate** somehow
6. **Paul’s architectural instinct:** a **core data specialist** holding **IDs and pointers** to validated core data — **not replicated**; validated core **overrides** what was seeded; **the same structure** should be used to **add** data to the system.
7. Paul: *“I know that’s a lot. I hope you can break it down into logical pieces we can reason over. The path isn’t at all clear to me.”*

---

## Grok — response (substance)

### 1. Four problems — don’t conflate them

| # | Problem | Example | Negotiation? |
|---|---------|---------|--------------|
| A | Near-miss resolution | Kalman vs Kalmans | Yes (suggestions) |
| B | Unknown entity | Paul Murphy not in system | Yes |
| C | Under-specified entity | Generic “Paul Murphy” — need employer before email research | Yes |
| D | Attribute research | “What’s his email?” | After bind |

Paul Murphy is **B → C → D**, not A.

### 2. When is seed “validated” today?

| Stage | Today |
|-------|--------|
| File load | `seed.json` trusted bootstrap; uuid5 `id` at load |
| Lookup | Exact match; no validation pass |
| Query | `name`/`employer` requestable like any attribute |
| Write | No public addition; seed doesn’t grow from queries |

**Today:** validation = **maintainer curated seed at bootstrap**. Runtime does not promote, correct, or create core identity.

**Target lifecycle discussed:**

```
bootstrap (seed) → provisional bind → validated core → specialist facts
```

Seed = **origin**, not necessarily **canonical** after the network has operated.

### 3. Seed ↔ specialist overlap (name the mess)

Three roles currently collapsed:

1. **Registry** — does this `id` exist? bind keys (name + employer)?
2. **Bootstrap** — what shipped in `seed.json`?
3. **Validated facts** — what the network concluded after operation?

Today (`architecture.md`, supervisor, `build_context`):

- Supervisor resolves **seed only**
- Context merges seed + specialist storage
- Specialists re-derive `id` from `context.seed`
- `name` / `employer` can live in seed **and** specialist storage

Paul is right: need a cleaner split before “add data” makes sense.

### 4. Layered model (design sketch)

```
Protocol layer (supervisor + negotiation outcomes)
  resolve → bind → scope → quote → commit → research
        ↓
Entity registry (one place per network)
  id, bind keys, validation state, pointers
  “Core” — not replicated
        ↓                    ↓
  seed.json (bootstrap)   specialist storage (extended attrs)
  provisional hints       email, title, address, …
```

**Entity registry** ≈ Paul’s “core data specialist” — may be **supervisor-owned store + thin arbiter**, not a full research specialist.

Registry responsibilities discussed:

- Allocate `id` on **bind** (not on first typo)
- Store **minimum binding record** (CRM: name + employer)
- Track per-field validation: `provisional` | `validated` | `rejected`
- Point to where facts live
- **Validated registry overrides seed**

Specialists own **extended** attributes; they **propose/validate** domain fields, not entity existence.

### 5. Paul Murphy — desired step-by-step

**Query 1:** `entity_key: "Paul Murphy"`, `requested_attributes: ["email"]`

1. Resolve — no match, no close suggestions → `outcome: entity_unknown`
2. Policy — CRM MVR requires `name` + `employer` before bind/research
3. Negotiate — “No record for Paul Murphy”; `required_fields: ["employer"]`; explain email research waits on bind; **no id, no specialists, no Tavily**

**Query 2:** caller supplies employer (same `thread_id`; protocol TBD)

4. Bind — provisional `id`; registry `{name, employer, state: provisional}`
5. Validate core — professional (+ demographic?) in **validation mode** (lightweight coherence check)
6. Scope / quote — classify email; future metering
7. Research — contact specialist

Same path for **networks without initial seed** (launch v2).

### 6. Who validates name vs employer? — three patterns

| Pattern | Idea |
|---------|------|
| A | Core registry **agent** — single SoT for id + bind fields |
| B | **Supervisor + registry file** — no extra agent |
| C | **Domain specialists** propose/validate; supervisor/registry **commits** |

Paul’s CRM split fits **C with registry arbiter**:

- Registry holds **committed** name + employer
- Professional validates employer; demographic validates name (assignment TBD)
- Supervisor/registry commits when network **MVR policy** satisfied
- No replication: specialists hold extended attrs only

### 7. Suggested build sequence (order matters)

| Phase | Deliverable |
|-------|-------------|
| 1 | Entity key **suggestions** (Kalman/Kalmans) |
| 2 | **Unknown entity** + `required_fields` negotiation (no persist) |
| 3 | **MVR policy** per network (`guide.md` / ontology — CRM = name+employer) |
| 4 | **Registry** store + provisional `id` on bind |
| 5 | **Validation orchestration** (professional + demographic cooperate) |
| 6 | **Gate research** until bind + validate |
| 7 | **Seed from queries** / growth / override seed file |
| 8 | **Metering / x402** on commit phases |

Paul Murphy design sits at **2–3**; Andrea Kalman at **1**.

### 8. Decisions to lock before code

1. Seed **bootstrap-only** after first bind? (leaning yes for growth networks)
2. Registry **storage shape** (`entities.json`, SQLite, specialist path — one writable source)
3. **MVR** global vs per-network? (per-network via guide/ontology)
4. Validation: sync-light LLM vs full research?
5. How caller supplies missing fields (`EntityQuery` extend vs thread state vs new tool)
6. **Conflict rule:** seed vs validated registry — registry wins when `validated`

### 9. Direct answer: when does seed get validated?

- **Today:** at network **bootstrap** (human/maintainer), not on query
- **Target:** seed is **unvalidated bootstrap** until registry marks bind fields validated
- **Queries** trigger validation at **bind time**, not every lookup
- **Specialist research** validates **extended** attributes, not entity existence

Paul’s core-data-specialist instinct = **registry + arbiter**; mistake would be duplicating research or holding email/linkedin in “core.”

---

## Paul — follow-up

- Asked Grok to **store this conversation in TODO** for future reference (distilled).
- Later: wants **full conversation preserved** too — not only TODO bullets — for context when picking up.

---

## Grok — TODO action taken

Added **Entity registry, validation & growth (design — important)**; refactored **Seed data vs specialists**, **Seed from Queries**, **Data addition** cross-links. Committed `d15bd91`.

---

## Relationship between the two conversation docs

| Doc | Primary question |
|-----|------------------|
| [entity-key-negotiation.md](2026-06-08-entity-key-negotiation.md) | Near-miss keys; suggest don’t resolve; negotiation + x402 phases |
| This doc | Unknown/under-specified entities; validation timing; registry; growth |

Both are **protocol-first**. Implementation of growth (Paul Murphy) **depends on** outcome enums and negotiation from the first doc, then registry/MVR from this one.

---

## Open questions (when picking this up)

- Is `entity_unknown` a separate outcome from `entity_key_unresolved` (suggestions)?
- Exact MVR definition mechanism per network
- Whether “core data specialist” is an agent, a store, or supervisor logic
- How validation cooperation works synchronously in demos vs async later
- Whether `seed.json` remains export/sync or becomes secondary to registry
- Public API shape for supplying binding fields (no `provided_data` on `EntityQuery` today)
# Negotiation phases & metering — Phase 9 spec (design only)

**Status:** Draft — questions for Paul  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slices 1–6 behavior stable (implementation: none or stub types only)

---

## Problem

Paul’s agent-to-agent model needs **priced commit** — cost reflects total work scoped, not a single attribute. Slices 1–6 define negotiation outcomes; Slice 9 designs how **x402-style metering** attaches without blocking the protocol track.

---

## Objective

**Design document only** — no billing integration, no mandatory code changes. Output: locked phase model, state machine sketch, free vs paid boundaries, and types stub list for Slice 10.

---

## Phase model (from conversations — proposal)

| Phase | Name | Slices today | Typical cost |
|-------|------|--------------|--------------|
| **A** | Discover / bind entity | 1–4 | Free |
| **B** | Scope attributes + ontology | 2, classify step | Free or cheap |
| **C** | Commit + research | 5–6 gate, specialists/Tavily | Paid |
| **D** | Deliver + follow-ups | assemble, re-query | Included or metered |

**Rule:** Phases A–B stay cheap — no Tavily until Phase C commit accepted.

---

## Negotiation state (proposal)

Per `thread_id` (or future session store):

```
discovering → binding → validating → scoping → quoted → committed → researching → delivered
```

Map to existing outcomes:

| State | Outcome examples |
|-------|------------------|
| discovering | `entity_key_unresolved`, `entity_unknown` |
| binding | `entity_bound_provisional`, `entity_under_specified` |
| validating | `entity_validated`, `found` + validation message |
| scoping | classify complete, no research |
| quoted | `quote_required` (Slice 10 stub) |
| committed | gate passes, specialists invoked |

---

## Quote object (proposal — design only)

```json
{
  "quote_id": "uuid",
  "thread_id": "...",
  "entity_id": "...",
  "scoped_attributes": ["email"],
  "estimated_units": 1,
  "expires_at": "ISO8601",
  "phase": "C"
}
```

Client accepts quote → commit → research runs. Reject → stay at scoping, no Tavily.

---

## Free vs paid boundaries (proposal)

| Action | Free? |
|--------|-------|
| Key suggestions | Yes |
| Unknown / required_fields | Yes |
| Provisional bind | Yes |
| Core validation (rule-based) | Yes |
| Classify attrs (no Tavily) | Yes |
| Specialist + Tavily research | No — requires quote accept (future) |

---

## Deliverables (Slice 9)

1. This spec locked after Paul answers
2. `docs/plans/entity-metering-integration.md` (or section in program doc) — integration notes for future x402
3. Type stubs list for Slice 10 (`Quote`, `NegotiationPhase` enum) — optional `.py` stubs, no runtime wiring

**No:** payment provider, HTTP 402 responses, wallet flows.

---

## Open questions for Paul

### Q9a — Quote granularity

| Option | Meaning |
|--------|---------|
| A | One quote per **research commit** (all scoped attrs in one Tavily batch) |
| B | Per-attribute quotes (email separate from title) |
| C | Per-phase only (Phase C lump sum); attrs listed for transparency |

### Q9b — Validation in free tier?

Confirm: core validation (Slice 5 rule-based) stays **free** before any quote?

| Option | Meaning |
|--------|---------|
| A | Yes — always free (proposal) |
| B | Free for first N entities per network |
| C | Metered from day one (unlikely for demo) |

### Q9c — Classify step placement

Is ontology classify (today’s supervisor classify) **Phase B** (pre-quote), always free?

| Option | Meaning |
|--------|---------|
| A | Yes — classify before quote, no Tavily |
| B | Classify after quote accept |
| C | Skip classify in metering model — gate on attrs list only |

### Q9d — Design doc location

| Option | Meaning |
|--------|---------|
| A | Expand this file + program doc cross-link |
| B | Separate `entity-metering-integration.md` for x402 partner handoff |
| C | Both — this file = phases; integration doc = wire protocol |

### Q9e — Stub types in repo?

| Option | Meaning |
|--------|---------|
| A | Markdown design only — no `.py` until Slice 10 |
| B | `src/protocol/negotiation.py` stubs (dataclasses, no imports in graph) |
| C | Stubs + MCP `describe_network` phase documentation strings |
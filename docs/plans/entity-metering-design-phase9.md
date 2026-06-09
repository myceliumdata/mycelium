# Negotiation phases & metering — Phase 9 spec (deferred)

**Status:** **Deferred** — Paul (June 2026): complete Slices 1–8 first; revisit metering design when protocol + growth are proven  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slices 1–6 behavior stable (implementation: none)

---

## Paul direction (June 2026)

- **Proceed with Slices 1–8** before any metering design or hooks land in code.
- Payment/quote decisions are **premature** — more conversation needed across use cases.
- **Q9a (quote granularity):** defer discussion.
- **Q9b (validation free tier):** keep core validation **free for now**; revisit when metering resumes.
- **Q9c (classify placement):** defer — tied to payment model not yet agreed.

Open questions Q9a–Q9e remain in this file for when Paul + Grok pick the thread back up. No Cursor prompt until spec is locked.

---

## Problem (unchanged — for future reference)

Paul’s agent-to-agent model needs **priced commit** — cost reflects total work scoped, not a single attribute. Slices 1–6 define negotiation outcomes; Slice 9 would design how **x402-style metering** attaches without blocking the protocol track.

---

## Phase model (proposal — not locked)

| Phase | Name | Slices today | Typical cost |
|-------|------|--------------|--------------|
| **A** | Discover / bind entity | 1–4 | Free |
| **B** | Scope attributes + ontology | 2, classify step | Free or cheap |
| **C** | Commit + research | 5–6 gate, specialists/Tavily | Paid |
| **D** | Deliver + follow-ups | assemble, re-query | Included or metered |

**Working assumption until locked:** Phases A–B stay cheap — no Tavily until Phase C commit accepted. Core validation (Slice 5) stays free.

---

## Open questions (deferred)

### Q9a — Quote granularity

- A: One quote per research commit
- B: Per-attribute quotes
- C: Per-phase lump sum

### Q9b — Validation in free tier?

- A: Always free *(Paul: yes for now)*
- B: Free for first N entities
- C: Metered from day one

### Q9c — Classify step placement

- A: Phase B, free, before quote
- B: After quote accept
- C: Skip classify in metering model

### Q9d — Design doc location

- A: This file + program doc
- B: Separate integration doc
- C: Both

### Q9e — Stub types in repo?

- A: Markdown only
- B: `negotiation.py` stubs
- C: Stubs + MCP strings
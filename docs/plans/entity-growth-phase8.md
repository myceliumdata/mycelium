# Seed from queries & network growth — Phase 8 spec (draft)

**Status:** Draft — questions for Paul  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slices 4–7

---

## Problem

Slices 4–7 establish bind, validate, gate, and boundary cleanup — but growth is still **implicit** (registry rows from bind). Slice 8 makes **network growth from queries** a first-class story: the store must grow, and launch v2 may start without bootstrap seed.

---

## Objective

- Document and harden the **growth path** already started in Slice 4 (bind → validate → research enriches specialists)
- Optional operator tooling: export registry bind rows → seed regen (not required for runtime)
- Prepare for **empty-seed networks** (launch v2 subset) without implementing full `network create` UX in this slice

**In scope:** registry as canonical store for grown entities; research results persist to specialist storage under validated `entity_id`.

**Out of scope (this slice):** empty-seed `network create` CLI flag; inter-network handoff; non-person schemas.

---

## Growth model (proposal)

```
Query bind (Slice 4)
  → validate (Slice 5)
  → research (Slice 6, gated)
  → specialist storage write (extended attrs)
  → registry row remains SoT for bind fields
```

**Seed role after growth:** bootstrap origin only. Validated registry overrides seed on conflict (program P4). Re-query resolves registry before seed.

---

## Behaviors (proposal)

| Scenario | Expected |
|----------|----------|
| Paul Murphy bind + validate + email research | Registry row + contact storage under `entity_id` |
| Re-query Paul Murphy @ Acme + email | Registry hit; attrs from specialist storage |
| Andrea Kalmans (seed only) | Unchanged — seed pre-validated for gate |
| Registry + seed same name, different employer | Two entities (Slice 4 bind key) |

---

## Launch v2 subset (proposal — deferred detail)

Networks may ship with **empty `seed.json`** once negotiation + registry + gate work (Slices 1–7). First queries establish entities via bind flow.

**This slice:** document the path + smoke test with minimal/empty seed fixture. **Not** required: new `network create` without `--seed` in CLI.

---

## Operator tooling (proposal)

Optional script or documented procedure:

- `export-growth-seed` — read `entities.json` validated rows → generate `seed.json` fragment for maintainer review
- Not automatic; operator-initiated sync only

---

## Tests (smoke)

- Full Paul Murphy arc: unknown → bind → validate → email → re-query returns assembled attrs
- Empty-seed fixture network: first bind creates registry; no seed dependency for grown entity
- Seed person unchanged after growth queries on other entities

---

## Open questions for Paul

### Q8a — Growth enrichment scope

When research completes, should Slice 8 **explicitly** persist specialist findings and link them in registry (e.g. `attr_sources`), or is **existing specialist storage** sufficient and this slice is mostly docs + smoke tests?

| Option | Meaning |
|--------|---------|
| A | Docs + smoke only — storage already works via Slices 6–7 |
| B | Add registry pointers (`attr_sources: { email: "contact" }`) for operator visibility |
| C | Broader — registry tracks last_researched timestamps per attr |

### Q8b — Empty-seed demo in this slice?

| Option | Meaning |
|--------|---------|
| A | Document only; test with existing CRM seed |
| B | Add `examples/networks/empty-crm/` fixture with `[]` seed + MVR; smoke test bind path |
| C | Defer empty-seed entirely to a later launch track |

### Q8c — Seed export tooling

| Option | Meaning |
|--------|---------|
| A | No script — document manual export in plan only |
| B | Minimal `bin/export-growth-seed` operator script |
| C | Defer to post-program polish |

### Q8d — Conflict: seed row vs grown registry entity

If seed has `Paul Murphy @ OldCo` and a query binds `Paul Murphy @ NewCo`, we already get two entities (Slice 4). Should Slice 8 add an **explicit** `seed_override` or `supersedes` link, or leave as separate rows forever?

| Option | Meaning |
|--------|---------|
| A | Separate rows — no linking |
| B | Registry field `supersedes_seed_id` when bind matches seed name but different employer |
| C | Defer — not needed for CRM demo |
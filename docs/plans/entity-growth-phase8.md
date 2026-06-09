# Seed from queries & network growth — Phase 8 spec

**Status:** Locked (Paul, June 2026) — Q8a only; Q8b–Q8d deferred to `TODO.md`  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slices 4–7  
**Cursor prompt:** `prompts/cursor/next/2026-06-09-1700-entity-growth-phase8.md`

---

## Problem

Slices 4–7 establish bind, validate, gate, and boundary cleanup — but growth is still **implicit** (registry rows from bind). Slice 8 makes **network growth from queries** a first-class story and introduces **data attribution** in the registry — a product differentiator Paul wants tracked from the start.

---

## Objective

- Harden the **growth path**: bind → validate → research → specialist storage under `entity_id`
- Extend registry with **attribute attribution metadata** (which specialist owns each attr, when last researched)
- End-to-end smoke test of the Paul Murphy arc
- Document growth model for operators and future admin UI

**Out of scope (deferred — see `TODO.md`):** empty-seed fixture networks, seed export tooling, seed-vs-grown entity linking across network types.

---

## Growth model (locked)

```
Query bind (Slice 4)
  → validate (Slice 5)
  → research (Slice 6, gated)
  → specialist storage write (extended attrs)
  → registry updates attr_sources + last_researched_at
```

**Seed role after growth:** bootstrap origin only. Validated registry overrides seed on conflict (program P4). Re-query resolves registry before seed.

---

## Registry schema extension (locked — Paul Q8a)

On successful specialist research for a validated or seed-pre-validated entity, registry arbiter (supervisor-owned) updates the entity row:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Paul Murphy",
  "employer": "Acme Corp",
  "validation_state": "validated",
  "attr_sources": {
    "email": "contact",
    "title": "professional"
  },
  "last_researched_at": {
    "email": "2026-06-09T14:30:00+00:00",
    "title": "2026-06-09T14:30:00+00:00"
  }
}
```

| Field | Meaning |
|-------|---------|
| `attr_sources` | Map attr name → specialist category slug that produced/stores the value |
| `last_researched_at` | Map attr name → ISO8601 UTC timestamp of last successful research write |

**Rules:**

- Update only attrs actually written in that research pass
- Seed-only entities (no registry row): optional mirror row on first research, or attribution on registry rows only — **implement for registry-grown entities**; seed hits may skip registry write unless already in `entities.json`
- Attribution is **registry metadata** — specialist storage remains SoT for attr values

**USP note:** Data attribution is a deliberate product capability; admin UI and MCP surfacing come later (`admin-ui-backlog.md`).

---

## Behaviors (locked)

| Scenario | Expected |
|----------|----------|
| Paul Murphy bind + validate + email research | Registry row + contact storage; `attr_sources.email = "contact"` |
| Re-query Paul Murphy @ Acme + email | Registry hit; attrs from specialist storage |
| Andrea Kalmans (seed only) | Unchanged — seed pre-validated for gate |
| Registry + seed same name, different employer | Two entities (Slice 4 bind key) — linking deferred |

---

## Tests (smoke)

- Full Paul Murphy arc: unknown → bind → validate → email → re-query returns assembled attrs
- Registry row contains `attr_sources` and `last_researched_at` after email research
- Seed person unchanged after growth queries on other entities

---

## Deferred (Paul — tracked in `TODO.md`)

| # | Topic | Reason |
|---|-------|--------|
| Q8b | Empty-seed demo fixture | Defer to launch v2 track |
| Q8c | `export-growth-seed` operator script | Post-program polish |
| Q8d | Seed vs grown entity linking (`supersedes`, etc.) | Needs multi-network-type design (CRM ≠ car parts) |

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| Q8a | **C — full attribution:** `attr_sources` + `last_researched_at` on registry rows |
| Q8b | Defer empty-seed demo → `TODO.md` |
| Q8c | Defer seed export tooling → `TODO.md` |
| Q8d | Defer seed/grown linking → `TODO.md` |
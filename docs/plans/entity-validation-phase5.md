# Core validation orchestration — Phase 5 spec (draft)

**Status:** Partially locked (Paul, June 2026) — Q5c/Q5d pending confirmation  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slice 4

---

## Problem

After provisional bind, CRM policy expects **name** and **employer** to be validated before attribute research. Paul wants demographic (name) and professional (employer) to cooperate under one registry `id` — not replicated in specialist storage.

---

## Objective

Run **sync-light validation** on provisional registry entities; promote `validation_state` and per-field states to `validated` when MVR passes. New outcome `entity_validated` when validation completes in-query.

**Bootstrap seed:** unchanged — pre-validated for gating (no validation pass).

---

## Validation orchestration (pattern C — locked)

| Role | Responsibility |
|------|----------------|
| **Demographic specialist** | Name plausibility check (validation mode) |
| **Professional specialist** | Employer plausibility check (validation mode) |
| **Registry arbiter** (supervisor-owned) | Commit field states; set entity `validation_state` |

Specialists do **not** own bind fields in storage after Slice 7; validation mode returns propose/accept signals only.

---

## Validation mode API (proposal)

Add optional flag on specialist invoke path when `validation_state == provisional`:

- Input: `current_id`, MVR fields from registry, `target_fields: ["name"]` or `["employer"]`
- Output: `validation_contrib: { field, status: pass|fail|pending, reason? }`
- **No Tavily** in validation mode

**CRM v1 rules (proposal — no LLM required for demo):**

| Field | Pass rule |
|-------|-----------|
| `name` | Non-empty, ≥2 chars, not all digits |
| `employer` | Non-empty, ≥2 chars |

LLM coherence check: **deferred** unless Paul wants in v1.

---

## When validation runs

**Proposal:** On query when:

1. Resolved entity is registry `provisional`, and  
2. Complete MVR present (bind satisfied), and  
3. Either no `requested_attributes` OR attrs requested (validation before research in Slice 6)

Same graph turn: bind (if needed) → validate → then gate research.

*Paul: confirm validate on every provisional resolve, or only when `requested_attributes` non-empty?*

---

## Outcomes

| Situation | `outcome` |
|-----------|-----------|
| All MVR fields pass | `entity_validated` |
| Any field fails | stay `provisional`; **proposal:** `outcome: found` with message explaining validation failed — no `validation_rejected` enum in v1 |
| Already validated | normal `found` / `assembled` |

**`entity_validated` response (proposal):**

```json
{
  "outcome": "entity_validated",
  "results": [{ "id": "…", "name": "Paul Murphy", "employer": "Acme Corp" }],
  "message": "Core record validated. Attribute research may proceed on subsequent queries.",
  "required_fields": []
}
```

Email in same request after validation in one turn — **Slice 6** decides; Slice 5 may validate only and defer research to next invoke.

---

## Registry updates

On pass: `validation_state: validated`, `field_states.*: validated`.

---

## Tests (smoke)

- Provisional Murphy @ Acme → validators pass → `entity_validated` in registry
- Absurd employer `""` → stay provisional, clear message
- Seed Andrea Kalmans → no validation invoke

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| Q5a | Validate on **every** query once MVR complete (even identity-only) |
| Q5b | Validator failure → stay **provisional**, explain in `message`; **no** `validation_rejected` outcome |
| Q5c | *Pending Paul confirmation after explanation* |
| Q5d | *Pending Paul confirmation after explanation* |
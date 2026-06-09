# Core validation orchestration — Phase 5 spec

**Status:** Locked (Paul, June 2026)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slice 4  
**Cursor prompt:** `prompts/cursor/next/2026-06-09-1400-entity-validation-phase5.md`

---

## Problem

After provisional bind, CRM policy expects **name** and **employer** to be validated before attribute research. Paul wants demographic (name) and professional (employer) to cooperate under one registry `id` — not replicated in specialist storage.

---

## Objective

Run **sync-light, rule-based validation** on provisional registry entities; promote `validation_state` and per-field states to `validated` when MVR passes. Outcome `entity_validated` when validation completes and no attribute research runs in the same turn.

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

## Validation mode API

Add optional flag on specialist invoke path when `validation_state == provisional`:

- Input: `current_id`, MVR fields from registry, `target_fields: ["name"]` or `["employer"]`
- Output: `validation_contrib: { field, status: pass|fail|pending, reason? }`
- **No Tavily** in validation mode
- **No LLM** in v1 — rule-based only (Paul Q5d)

**CRM v1 rules:**

| Field | Pass rule |
|-------|-----------|
| `name` | Non-empty, ≥2 chars, not all digits |
| `employer` | Non-empty, ≥2 chars |

LLM coherence check: **deferred** (not in v1).

---

## When validation runs (locked)

On **every** query when:

1. Resolved entity is registry `provisional`, and  
2. Complete MVR present (bind satisfied)

Runs even for identity-only queries (no `requested_attributes`) — Paul Q5a.

**Same graph turn (locked — Paul Q5c, aligned with Slice 6 Q6b):**

```
bind (if needed) → validate → research (if validated and attrs requested)
```

Slice 5 owns the validate step; Slice 6 owns the gate that allows research immediately after validation in the same run.

When `requested_attributes` non-empty and validation passes, final outcome is **`assembled`** / **`found`** with attrs (Slice 6), not `entity_validated`.

---

## Outcomes

| Situation | `outcome` |
|-----------|-----------|
| All MVR fields pass; no attrs requested | `entity_validated` |
| All MVR fields pass; attrs requested | defer to Slice 6 — `assembled` / `found` with attrs |
| Any field fails | stay `provisional`; `found` + message explaining validation failed |
| Already validated | normal `found` / `assembled` |

**No `validation_rejected` outcome in v1** — Paul Q5b.

**`entity_validated` response:**

```json
{
  "outcome": "entity_validated",
  "results": [{ "id": "…", "name": "Paul Murphy", "employer": "Acme Corp" }],
  "message": "Core record validated.",
  "required_fields": []
}
```

---

## Registry updates

On pass: `validation_state: validated`, `field_states.*: validated`.

---

## Tests (smoke)

- Provisional Murphy @ Acme → validators pass → `entity_validated` in registry (identity-only query)
- Provisional Murphy @ Acme + email → validate then research same turn → `assembled` / attr values (with Slice 6)
- Absurd employer `""` → stay provisional, clear message
- Seed Andrea Kalmans → no validation invoke

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| Q5a | Validate on **every** query once MVR complete (even identity-only) |
| Q5b | Validator failure → stay **provisional**, explain in `message`; **no** `validation_rejected` outcome |
| Q5c | **Same turn:** bind → validate → research when validated (Slice 6 gate) |
| Q5d | **Rule-based validation only** in v1 (no LLM plausibility) |
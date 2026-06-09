# Unknown entity + MVR policy — Phase 3 spec (draft)

**Status:** Locked (Paul, June 2026)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slices 1–2  
**Cursor slice:** TBD after Paul approves batch 1

---

## Problem

**Paul Murphy** is not in seed. Today: `not_found` + if `email` requested, supervisor still classifies and may invoke specialists (Tavily spend). Paul wants structured negotiation: unknown entity, ask for employer (CRM MVR), no research until bound.

**Distinct from Slice 1:** Kalman/Kalmans → `entity_key_unresolved` (near-miss). Murphy → `entity_unknown` (no close suggestion).

---

## Objective

Declare per-network **MVR** (minimum viable record). On unknown entity, return `entity_unknown` + `required_fields`. Short-circuit before classification and specialists. **No persistence.**

---

## MVR declaration (locked: `network.json`)

Extend `<network_root>/network.json`:

```json
{
  "name": "crm",
  "display_name": "CRM example",
  "mvr": {
    "bind_fields": ["name", "employer"],
    "name_source": "entity_key",
    "description": "CRM people: display name plus current employer before bind and research."
  }
}
```

| Field | Meaning |
|-------|---------|
| `bind_fields` | Ordered list of fields required to bind an entity |
| `name_source` | `"entity_key"` — name for bind comes from `EntityQuery.entity_key` (Slice 3); not supplied in `binding` |
| `description` | Agent-facing text in `describe_network` / capabilities |

**CRM fallback:** If `mvr` absent, use same default (`name` + `employer`, `name_source: entity_key`). Update committed `examples/networks/crm/network.json` with `mvr` block.

**Loader:** `src/network/mvr.py` (or `network/manifest.py`) — `load_mvr(paths) -> MvrPolicy`.

---

## Resolution order (after Slice 1)

```
1. Exact seed/registry match     → existing flow
2. entity_key_unresolved (suggest) → Slice 1 short-circuit
3. entity_unknown                → this slice
```

Registry lookup not in Slice 3 (Slice 4). Seed exact + suggest only.

---

## New `QueryResponse` fields

| Field | Type | Slice 3 |
|-------|------|---------|
| `required_fields` | `list[str]` | MVR field names still needed (excludes `name` when `name_source=entity_key`) |

**Example — CRM Paul Murphy + email:**

```json
{
  "outcome": "entity_unknown",
  "results": [],
  "required_fields": ["employer"],
  "suggestions": [],
  "message": "No record for 'Paul Murphy'. To research email, provide employer (who they work for). Re-query with the same entity_key when you have it.",
  "thread_id": "…"
}
```

---

## `entity_under_specified` — deferred to Slice 4 (locked)

Slice 3 ships **`entity_unknown` only**. `entity_under_specified` first appears in Slice 4 when `EntityQuery.binding` is partial.

---

## Supervisor short-circuit

On `entity_unknown` (after resolution order above):

- **No** `get_category_tree().classify()`
- **No** `specialists_to_invoke`
- Route → `assemble_response` → `response_entity_unknown()`

Same graph pattern as Slice 1 `entity_key_unresolved`.

---

## `required_fields` computation

Given MVR `bind_fields: ["name", "employer"]` and `name_source: entity_key`:

- `name` satisfied by non-empty `entity_key`
- `required_fields` = bind_fields not satisfied → `["employer"]` for CRM

If `entity_key` empty → treat as invalid query (`not_found` or validation error — **see open question**).

---

## MCP / describe_network

Add to `build_network_capabilities().policy`:

- `entity_unknown` — meaning + `required_fields` usage
- `mvr` — expose loaded MVR summary from `network.json`
- Cross-link: after near-miss resolution (Slice 1), unknown path (this slice)

---

## Tests (smoke)

| Case | Expected |
|------|----------|
| `Paul Murphy` + `email` | `entity_unknown`, `required_fields=["employer"]`, no specialist audit lines |
| `Andrea Kalman` + `email` | `entity_key_unresolved` (Slice 1, not unknown) |
| `Aaron Holiday` + `email` | normal assembled path |
| `NoSuchPerson-xyz` + no close suggest | `entity_unknown` (not bare `not_found`) |

---

## Explicit non-goals

- `EntityQuery.binding` (Slice 4)
- Registry / persist
- `entity_under_specified` (Slice 4)
- Research gate for seed hits (Slice 6)

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| Q3a | Zero match + no suggestions → **`entity_unknown`**; bare `not_found` only for empty/invalid `entity_key` |
| Q3b | **`entity_under_specified` in Slice 4 only** |
| Q3c | Identity-only unknown → **`entity_unknown` + `required_fields`** |
| Q3d | Add **`mvr` to `examples/networks/crm/network.json`** in this slice |
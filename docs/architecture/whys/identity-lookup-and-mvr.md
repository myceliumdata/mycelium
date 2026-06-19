# Why identity, lookup, and MVR are separate

**Status:** Shipped (MVR redesign M1–M10, June 2026)  
**Mechanics:** [`architecture.md`](../../architecture.md) § MVR redesign · [`mvr-best-practices.md`](../../plans/mvr-best-practices.md) · [`mvr-redesign-program.md`](../../plans/mvr-redesign-program.md)

---

## The short answer

Three concerns that were once conflated in `entity_key`, `binding`, and `name_source` are now explicit:

| Concern | Meaning | Client input |
|---------|---------|--------------|
| **Identity** | Stable **`id` (UUID)** for a registry row | `id` on step 1 (or obtain from step-2 `results[]`) |
| **Lookup** | Find candidates by **partial field match** (AND within map) | `lookup: { field: value, … }` on step 1 |
| **MVR** | Network-defined **minimum field set** to **create** a row and **run extended research** | Full `bind_fields` in step-1 `lookup` when creating |

Lookup fields are any subset of indexed MVR bind fields. MVR is the full set — required together only for create and research gating.

---

## What problem we were solving

| Conflation | Failure mode |
|------------|--------------|
| Name string as identity | “Kevin Zhang” is not unique; merges and splits become ambiguous |
| Lookup = create | Partial `{name: Kevin}` accidentally provisions rows |
| MVR = search filter | Requiring full MVR for every query blocks legitimate broad searches (`employer=IBM` → 237 matches) |
| `entity_key` negotiation | Human-oriented string matching mixed with machine bind maps |

Separating the three lets agents **search loosely**, **commit narrowly**, and **create only with intent**.

---

## Identity: UUID only

Public protocol identity is always `id` (uuid4 assigned at bootstrap or create-on-deliver).

- Lahman `playerID`, email addresses, and display names are **not** parallel public handles — they are source metadata, bind values, or research outputs depending on network.
- Step 1 with `id` still returns `delivery_id` (same two-step contract).
- Unknown or expired `id` → `not_found`.

**Why:** stable joins across specialist storage, re-import, and multi-match batch deliver without renaming rows when bind fields are corrected.

---

## Lookup: partial match is valid

`lookup` keys must be ⊆ `mvr.bind_fields` for the inferred record type. AND semantics within the map.

| Example | Expected |
|---------|----------|
| `{employer: IBM}` | Many matches — valid |
| `{name: Andrea Kalmans}` | One or few matches |
| `{player: Hank Aaron}` | Baseball partial — unique or homonym multi-match |
| `{player, debut_team, debut_year}` | Full player MVR — precise |

Zero hits trigger fuzzy → LLM alias (on `bootstrap_only`) → incomplete / create / not_found per policy — not automatic row creation.

**Why:** agents explore breadth first; commitment (create, research, batch) happens on step 2 via scoped `delivery_id`.

---

## MVR: create and research gate

`network.json` declares per record type:

```json
"mvr": {
  "record_types": {
    "person": {
      "bind_fields": ["name", "employer"]
    }
  }
}
```

MVR answers: *“What must we know before this network will add a new entity and research extended attributes?”*

| Situation | Outcome |
|-----------|---------|
| Partial lookup, 0 hits, `query_allowed` (CRM) | `lookup_incomplete` + `required_fields` or fuzzy `lookup_suggested` |
| Full MVR lookup, 0 hits, `query_allowed` | `lookup_resolved` with `create_on_deliver: true` |
| Partial/full lookup, 0 hits, `bootstrap_only` (baseball) | Fuzzy / LLM alias; never `create_pending` |
| Full MVR, 1+ hits | Normal resolve → deliver |

**Designer tradeoff:** loose MVR (name only) eases create but increases collisions; tight MVR (name + employer + employee_id) improves disambiguation but raises client burden. Mycelium does not mandate CRM’s shape — each network chooses.

---

## How the three interact on step 1

```text
lookup (partial or full)  →  index resolve  →  total_matches
                         →  delivery_id scopes: ids[], attrs, create flag

id                       →  direct resolve  →  delivery_id (1 entity)

full MVR + 0 hits        →  create_on_deliver ticket (if policy allows)
partial + missing fields →  lookup_incomplete (CRM) or alias path (baseball)
```

Extended `requested_attributes` bind on step 1 only — they define deliver workload, not lookup shape. See [two-step-query-protocol.md](two-step-query-protocol.md).

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| `entity_key` string primary key | Ambiguous; poor batch and metering semantics |
| Require full MVR for all lookups | Blocks legitimate broad queries |
| `name_source` in `network.json` | Special-cased one field; `name` is a normal bind field |
| `binding` blob on step 2 | Workload mutation after resolve |
| Global MVR across networks | Each network defines its own collision / research tradeoff |

---

## Related

- Multi-record-type lookup routing: [multi-record-type-routing.md](multi-record-type-routing.md)
- Registry cache vs specialist truth: [three-layer-storage-model.md](three-layer-storage-model.md)